from setuptools import setup

setup(
    name='lakehead',
    version="0.0.1",
    description = ('Lakehead is a utility for creating an RPM based '
                   'system packaging pipeline.'),
    author = 'Martin Walsh',
    author_email = 'sysadm@mwalsh.org',
    license = 'BSD',
    long_description = ('Lakehead is a utility for creating an RPM based '
                        'system packaging pipeline.'),
    packages = ['lakehead'],
    entry_points = {        
        'console_scripts': [
            'lakehead = lakehead:main',
            ]
        },
)
