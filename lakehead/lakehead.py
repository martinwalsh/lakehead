#!/usr/bin/env python
import os as _os
from contextlib import contextmanager

__all__ = ['chdir', 'main']

@contextmanager
def chdir(path, makedirs=False):
    cwd = _os.getcwd()
    try:
        if makedirs and not _os.path.isdir(path):
            _os.makedirs(path)
        _os.chdir(path)
        yield path
    finally:
        _os.chdir(cwd)

def main(*args):
    print args
