#!/usr/bin/env python
import os
import sys
import json
import types
import shutil
import tempfile
import optparse

from glob import glob
from subprocess import Popen
from urllib import urlretrieve
from contextlib import contextmanager

__all__ = ['chdir', 'main']

@contextmanager
def chdir(path, makedirs=False):
    cwd = os.getcwd()
    try:
        if makedirs and not os.path.isdir(path):
            os.makedirs(path)
        os.chdir(path)
        sys.stdout.write('++ (%s) cd %s\n' % (cwd, path))
        sys.stdout.flush()
        yield path
    finally:
        os.chdir(cwd)

@contextmanager
def mktmpdir(preserve=False, prefix='lakehead'):
    try:
        tmpdir = tempfile.mkdtemp(prefix=prefix)
        yield tmpdir
    finally:
        if not preserve:
            shutil.rmtree(tmpdir, ignore_errors=True)
    
class Config(object):
    def __init__(self, project_name):
        with open('%s.json' % project_name) as f:
            d = json.load(f)
        self.keys = d.keys()
        self.__dict__.update(d)

    def __getitem__(self, key):
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(repr(key))

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def dict(self):
        return dict((k, getattr(self, k)) for k in self.keys) 

class BadExitStatus(StandardError): pass
def spawn(cmd):
    sys.stdout.write('++ %s\n' % ' '.join(cmd))
    sys.stdout.flush()
    process = Popen(cmd)
    process.communicate()
    if process.poll():
        raise BadExitStatus(cmd)

def buildSRPM(**kwds):
    cmd = ('/usr/bin/mock --configdir=%(configdir)s -r mock'
           ' --buildsrpm --spec=%(spec)s'
           ' --resultdir=%(resultdir)s'
           ' --sources=%(sourcedir)s' % kwds).split()
    spawn(cmd)

def buildRPM(**kwds):
    cmd = ('/usr/bin/mock --configdir=%(configdir)s -r mock'
           ' --rebuild --resultdir %(resultdir)s %(resultdir)s/'
           '%(name)s-%(version)s-%(release)s.%(dist)s.src.rpm' % kwds).split()
    spawn(cmd)

def get_abspath(relpath, base=None):
    if base is None:
        base = os.getcwd()
    return os.path.realpath(os.path.abspath(os.path.join(base, relpath)))

# This works for local/relative paths also
def download(src, dst):
    urlretrieve(src, dst)

# local path sources should be absolute
def download_to_cwd(sources):
    if type(sources) in types.StringTypes:
        sources = [sources]
    for source in sources:
        download(source, os.path.basename(source))

def update_repo(srpm, rpms):
    with chdir('/var/www/repo'):
        with chdir('SRPMS'):
            download_to_cwd(srpm)
            spawn('/usr/bin/createrepo --update .'.split())

        with chdir('RPMS'):
            for fname in rpms:
                if 'noarch' in fname:
                    with chdir('noarch'):
                        download_to_cwd(fname)
                        spawn('/usr/bin/createrepo --update .'.split())
                else:
                    with chdir('x86_64'):
                        download_to_cwd(fname)
                        spawn('/usr/bin/createrepo --update .'.split())

def build(opts):
    # load default mock config
    mock_config = glob(get_abspath('mock/*'))

    with chdir(opts.project):
        config = Config(opts.project)

        project_dir = os.getcwd()
        spec_file = get_abspath('%(name)s.spec' % config)
        mock_config.extend(glob(get_abspath('mock/*')))

        with mktmpdir(opts.debug) as configdir:
            with chdir(configdir):
                download_to_cwd(mock_config)

            with mktmpdir(opts.debug) as resultdir:
                with mktmpdir(opts.debug) as sourcedir:
                    with chdir(sourcedir):
                        download_to_cwd(config.source)
                        for pattern in config.other_sources:
                            download_to_cwd(
                                glob(get_abspath(pattern, project_dir))
                            )
                        buildSRPM(
                            configdir=configdir, resultdir=resultdir,
                            sourcedir=sourcedir, spec=spec_file, 
                            **config.dict())
                        buildRPM(
                            configdir=configdir, 
                            resultdir=resultdir, **config.dict())

                with chdir(resultdir):
                    srpm = get_abspath(glob('*.src.rpm')[0])
                    rpms = [get_abspath(rpm) for rpm in glob('*.rpm')]
                    rpms.remove(srpm)
                    update_repo(srpm, rpms)

def main():
    parser = optparse.OptionParser()
    parser.add_option('-p', '--project', help='Build project name.')
    parser.add_option('-d', '--debug', default=False, action='store_true',
                        help='Turn on debugging, do not delete tempfiles')
    opts, args = parser.parse_args()

    build(opts)
