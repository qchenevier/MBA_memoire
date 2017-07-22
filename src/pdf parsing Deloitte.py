import pandas as pd
import seaborn as sns
import numpy as np
import xmltodict
import re
import logging

from lxml import etree
from sklearn import cluster
from bokeh.charts import Scatter, output_file, show
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
            'y_class': lambda s: s.mean(),
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
            'y': lambda s: s.mean(),
            'dbscan_class': lambda s: s.mean(),
            'line_number': lambda s: s.min(),
        })
        .sort_values(by='y', ascending=False)
        .assign(text=lambda df: df.text.str.replace('- ', ''))
    )


def _filter_junk_data(df):
    return (
        df
        .loc[lambda df: df.x > 200]
        .loc[lambda df: (df.x > 500) | (df.y < 1500)]
    )


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

xml_file = 'Deloitte_light_raw.xml'
xml_filepath = path.find_files(xml_file)[0]
tree = etree.parse(str(xml_filepath))
dom = tree.getroot()
namespace = dom.nsmap

# dom.xpath('/*', namespaces=namespace)
# dom.xpath('/pages/*', namespaces=namespace)
# dom.xpath('/pages/page/*', namespaces=namespace)
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
dbscan_kwargs = dict(eps=10, min_samples=1)
# dbscan_kwargs = dict(eps=15, min_samples=1)
df = (
    df_raw
    .pipe(_compute_x_y)
    .pipe(_filter_junk_data)
    .pipe(_select_x_y, 320, 5000, 0, 1250)
    # .pipe(_simplify_font)
    .pipe(_global_clustering, **dbscan_kwargs)
    .pipe(_apply_function_to_dbscan_classes, _aggregate_lines, **meanshift_kwargs)
    .pipe(_apply_function_to_dbscan_classes, _merge_similar_lines)
)
df

df.to_excel(str(path.data / 'xlsx' / re.sub('xml', 'xlsx', xml_file)), index=False)
df.to_csv(str(path.data / 'csv' / re.sub('xml', 'csv', xml_file)), index=False, encoding='utf-8-sig')

# PLOTS
%matplotlib inline
# sns.lmplot('x', 'y', data=df, hue='font', fit_reg=False)
sns.lmplot('x', 'y', data=df, hue='dbscan_class', fit_reg=False, legend=False)
