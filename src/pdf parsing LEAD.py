import pandas as pd
import seaborn as sns
import numpy as np
import xmltodict
import re
import logging

from lxml import etree
from sklearn import cluster
from bokeh.charts import Scatter, output_file, show
from scipy.spatial.distance import cdist
from settings import path


def _compute_x_y(df):
    return (
        pd.concat([
            df,
            df.bbox.str.extract(r'(.*),(.*),(.*),(.*)')
        ], axis=1)
        .rename(columns={0: 'xmin', 1: 'ymin', 2: 'xmax', 3: 'ymax'})
        .assign(x=lambda df: (df.xmin.astype('float') + df.xmax.astype('float')) / 2)
        .assign(y=lambda df: (df.ymin.astype('float') + df.ymax.astype('float')) / 2)
        .drop(['xmin', 'ymin', 'xmax', 'ymax', 'bbox'], axis=1)
    )


def _select_x_y(df, xmin, xmax, ymin, ymax):
    return (
        df
        .loc[lambda df: df.x > xmin]
        .loc[lambda df: df.x < xmax]
        .loc[lambda df: df.y > ymin]
        .loc[lambda df: df.y < ymax]
    )


def _clusterized_column(df, column, **kwargs):
    res = cluster.mean_shift(pd.DataFrame(df[column]).values, **kwargs)
    return res[1]


def _clusterize_column(df, column, **kwargs):
    new_column = kwargs.pop('new_column', column)
    return (
        df
        .assign(**{new_column: _clusterized_column(df, column, **kwargs)})
    )


def _global_clustering(df, **dbscan_kwargs):
    return df.assign(
        dbscan_class=lambda df: cluster.dbscan(df[['x', 'y']], **dbscan_kwargs)[1])


def _simplify_font(df):
    return df.assign(font=lambda df: df.font.apply(lambda x: x[0:6]))


def _aggregate_lines(df, **kwargs):
    return (
        df
        .pipe(_clusterize_column, column='y', new_column='y_class', **kwargs)
        .groupby('y_class')
        .agg({
            'font': lambda s: s.iloc[0],
            'size': lambda s: s.iloc[0],
            'text': lambda s: s.str.cat(),
            'x': lambda s: s.mean(),
            'y': lambda s: s.mean(),
            'dbscan_class': lambda s: s.mean(),
            # 'y_class': lambda s: s.mean(),
        })
        .sort_values(by='y', ascending=False)
        .assign(line_number=lambda df: np.arange(len(df)))
    )


def _apply_function_to_dbscan_classes(df, function, **kwargs):
    return (
        df
        .groupby('dbscan_class')
        .apply(function, **kwargs)
        .reset_index(drop=True)
    )


def _merge_similar_lines(df):
    return (
        df
        .groupby('font')
        .agg({
            'font': lambda s: s.iloc[0],
            'size': lambda s: s.iloc[0],
            'text': lambda s: s.str.cat(sep=' '),
            'x': lambda s: s.mean(),
            'y': lambda s: s.max(),
            'dbscan_class': lambda s: s.mean(),
            'line_number': lambda s: s.min(),
        })
        .sort_values(by='y', ascending=False)
    )


def _closest_node(node, nodes):
    return nodes[cdist([node], nodes).argmin()]


def _find_dbscan_class_from_closest(r, df):
    closest_xy = _closest_node(r.loc[['x', 'y']].values, df.loc[:, ['x', 'y']].values)
    return df.loc[lambda df: (df.x == closest_xy[0]) & (df.y == closest_xy[1]), 'dbscan_class'].item()


def _assign_dbscan_class_from_closest(df, df_to_search, new_column='dbscan_class'):
    return df.assign(**{
        new_column: lambda df: df.apply(_find_dbscan_class_from_closest, args=(df_to_search,), axis = 1)
    })


def _keep_text(df):
    return df.loc[lambda df: ~df.font.str.contains('OMMPZL'), :]


def _keep_tags(df):
    return df.loc[lambda df: df.font.str.contains('OMMPZL'), :]


def _clusterize_xy(df, **meanshift_kwargs):
    return (
    df
    .pipe(_clusterize_column, column='y', new_column='y_class', **meanshift_kwargs)
    .pipe(_clusterize_column, column='x', new_column='x_class', **meanshift_kwargs)
    .groupby('y_class')
    .apply(lambda df: df.assign(y=lambda df: df.y.mean()))
    .reset_index(drop=True)
    .groupby('x_class')
    .apply(lambda df: df.assign(x=lambda df: df.x.mean()))
    .reset_index(drop=True)
    .drop(['y_class', 'x_class'], axis=1)
)


def _find_Category_from_closest_x(r, df, new_column):
    closest_x = _closest_node(r.loc[['x']].values, df.loc[:, ['x']].values)
    return df.loc[lambda df: df.x == closest_x[0], new_column].item()


def _assign_Category_from_closest_x(df, df_to_search, new_column='Category'):
    return df.assign(**{
        new_column: lambda df: df.apply(
            _find_Category_from_closest_x,
            args=(df_to_search, new_column),
            axis=1)
    })


def _extract_text(df):
    return (
        df
        .loc[:, ['dbscan_class', 'text', 'line_number']]
        .pivot(index='dbscan_class', columns='line_number', values='text')
        .rename(columns={0: 'tags', 1: 'Operational_Competency', 2: 'Action'})
        .reset_index()
        .pipe(
            pd.merge,
            df.loc[lambda df: df.line_number == 0, ['dbscan_class', 'x', 'y']],
            on='dbscan_class',
        )
        .drop(['dbscan_class'], axis=1)
    )


def _extract_tags(df):
    return (
        df
        .pipe(lambda df: df.join(df.tags.str.split(' ', expand=True)))
        .rename(columns={
            0: 'Executive',
            1: 'Value_model',
            2: 'Level',
            3: 'Competency',
            4: 'IT_tool',
            5: 'Service_type',
        })
        .drop(['tags'], axis=1)
    )


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

xml_file = 'LEAD_light_raw.xml'
xml_filepath = path.find_files(xml_file)[0]
tree = etree.parse(str(xml_filepath))
dom = tree.getroot()
namespace = dom.nsmap

# dom.xpath('/*', namespaces=namespace)
# dom.xpath('/pages/*', namespaces=namespace)
# dom.xpath('/pages/page/rect', namespaces=namespace)
# dom.xpath('/pages/page/text', namespaces=namespace)
rects = dom.xpath('/pages/page/rect', namespaces=namespace)
texts = dom.xpath('/pages/page/text', namespaces=namespace)
# len(dom.findall('.//text', namespaces=namespace))
# len(dom.findall('.//rect', namespaces=namespace))
# findall_kwargs = dict(namespaces=namespace)

df_raw = pd.DataFrame.from_records(
    [{**dict(text_obj.attrib), **{'text': text_obj.text}} for text_obj in texts]
)

meanshift_kwargs = dict(bandwidth=2, cluster_all=True)
dbscan_kwargs = dict(eps=23, min_samples=1)
df_cat = (
    df_raw
    .pipe(_compute_x_y)
    .pipe(_select_x_y, 2100, 7400, 2350, 2450)
    .pipe(_simplify_font)
    .pipe(_global_clustering, **dbscan_kwargs)
    .pipe(_apply_function_to_dbscan_classes, _aggregate_lines, **meanshift_kwargs)
    .pipe(_apply_function_to_dbscan_classes, _merge_similar_lines)
    .loc[:, ['x', 'text']]
    .rename(columns={'text': 'Category'})
)
df_cat

meanshift_kwargs = dict(bandwidth=2, cluster_all=True)
dbscan_kwargs = dict(eps=40, min_samples=1)
df_big_cat = (
    df_raw
    .pipe(_compute_x_y)
    .pipe(_select_x_y, 2100, 7400, 2450, 2550)
    .pipe(_simplify_font)
    .pipe(_global_clustering, **dbscan_kwargs)
    .pipe(_apply_function_to_dbscan_classes, _aggregate_lines, **meanshift_kwargs)
    .pipe(_apply_function_to_dbscan_classes, _merge_similar_lines)
    .loc[:, ['x', 'text']]
    .rename(columns={'text': 'Big_Category'})
    .sort_values('x')
)
df_big_cat

meanshift_kwargs = dict(bandwidth=2, cluster_all=True)
dbscan_kwargs = dict(eps=23, min_samples=1)
df_text = (
    df_raw
    .pipe(_compute_x_y)
    .pipe(_select_x_y, 2100, 7400, 850, 2350)
    .pipe(_simplify_font)
    .pipe(_keep_text)
    .pipe(_global_clustering, **dbscan_kwargs)
    .pipe(_apply_function_to_dbscan_classes, _aggregate_lines, **meanshift_kwargs)
    .pipe(_apply_function_to_dbscan_classes, _merge_similar_lines)
)
df_text

meanshift_kwargs = dict(bandwidth=2, cluster_all=True)
dbscan_kwargs = dict(eps=10, min_samples=1)
df_tags = (
    df_raw
    .pipe(_compute_x_y)
    .pipe(_select_x_y, 2100, 7400, 850, 2350)
    .pipe(_simplify_font)
    .pipe(_keep_tags)
    .pipe(_global_clustering, **dbscan_kwargs)
    .pipe(_apply_function_to_dbscan_classes, _aggregate_lines, **meanshift_kwargs)
    .pipe(_assign_dbscan_class_from_closest, df_text.loc[lambda df: df.line_number == 0, :])
    .sort_values(by='x')
    .pipe(_apply_function_to_dbscan_classes, _merge_similar_lines)
)
df_tags

df_text_and_tags = (
    df_text
    .assign(line_number=lambda df: df.line_number + 1)
    .append(df_tags)
    .sort_values(by=['dbscan_class', 'line_number'])
)
df_text_and_tags

meanshift_kwargs = dict(bandwidth=2, cluster_all=True)
df = (
    df_text_and_tags
    .pipe(_extract_text)
    .pipe(_extract_tags)
    .pipe(_clusterize_xy, **meanshift_kwargs)
    .pipe(_assign_Category_from_closest_x, df_cat)
    .pipe(_assign_Category_from_closest_x, df_big_cat, new_column='Big_Category')
)
df

df.to_excel(str(path.data / 'xlsx' / re.sub('xml', 'xlsx', xml_file)))

# PLOTS
%matplotlib inline
sns.lmplot('x', 'y', data=df, hue='Big_Category', fit_reg=False)
