# simplepath.py
from pathlib import Path
import logging
import re

HERE = Path.cwd()
PARENT = Path.cwd().parent


def match_parents(path, pattern):
    return any([p.match(pattern) for p in path.parents])


class SimplePath:
    def __init__(self, root='here', pattern_to_hide=['__*__', '.*']):
        self.__pattern_to_hide__ = pattern_to_hide
        self._set_root(root)
        self._set_dir_names_as_attributes()

    def _set_dir_names_as_attributes(self):
        for path in self.find_dirs():
            if hasattr(self, path.name):
                logging.warning('Several matching folders for {}'.format(path.name))
            setattr(self, path.name, path)

    def _set_root(self, root):
        if isinstance(root, Path):
            self.root = root
        else:
            if root == 'parent':
                self.root = Path.cwd().parent
            elif root == 'here':
                self.root = Path.cwd()
            else:
                raise ValueError("root should be pathlib.Path object or 'here' or 'parent'")

    def _is_hidden(self, path):
        return any([path.match(pattern) or match_parents(path, pattern)
                    for pattern in self.__pattern_to_hide__])

    def find_dirs(self, pattern='*'):
        return [path for path in self.root.rglob(pattern)
                if path.is_dir() and not self._is_hidden(path)]

    def find_files(self, pattern='*'):
        return [path for path in self.root.rglob(pattern)
                if path.is_file() and not self._is_hidden(path)]
