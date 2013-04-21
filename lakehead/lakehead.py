#!/usr/bin/env python
import os
import json
import shutil
import tempfile
import optparse

from urllib import urlretrieve
from contextlib import contextmanager
from subprocess import Popen, PIPE, STDOUT

__all__ = ['chdir', 'main']

@contextmanager
def chdir(path, makedirs=False):
    cwd = os.getcwd()
    try:
        if makedirs and not os.path.isdir(path):
            os.makedirs(path)
        os.chdir(path)
        yield path
    finally:
        os.chdir(cwd)

@contextmanager
def mktmpdir(prefix='lakehead'):
    try:
        tmpdir = tempfile.mkdtemp(prefix=prefix)
        yield tmpdir
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    
class Config(object):
    def __init__(self, project_name):
        with open('%s.json' % project_name) as f:
            d = json.load(f)
        self.__dict__.update(d)

    def __getitem__(self, key):
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(repr(key))

    def __setitem__(self, key, value):
        setattr(self, key, value)

def buildsrpm(opts):
    cwd = os.getcwd()
    with chdir(opts.project):
        config = Config(opts.project)
        config.configdir = cwd
        if os.path.exists('mock.cfg'):
            config.configdir = os.getcwd()

        with mktmpdir() as sources:
            with chdir(sources):
                urlretrieve(config.source)

            config.sources = sources
            mock_cmd = ('/usr/bin/mock --configdir=%(configdir)s -r mock'
                        ' --buildsrpm --spec=%(name)s.spec'
                        ' --sources=%(sources)s' % config).split()
            mock = Popen(mock_cmd, stdout=PIPE, stderr=STDOUT)
            stdout, _ = mock.communicate()
            print stdout

def main():
    parser = optparse.OptionParser()
    parser.add_option('-p', '--project', help='Build project name.')
    opts, args = parser.parse_args()

    buildsrpm(opts)
