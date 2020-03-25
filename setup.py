
from setuptools import setup

__version__ = "0.1.2"

setup(
    name="SpaceDiary",
    version=__version__,
    description="Logging utility for Atevent Space",
    author="Michal Mazurek",
    author_email="michal@mazurek-inc.co.uk",
    url="",
    packages=['space_diary'],
    scripts=['bin/space_diary', 'bin/space_diary_config_install'],
    install_requires=[
        'pydash',
        'couchdb',
        'pyyaml',
        'celery[redis]',
        'colorama'
        ]
)
