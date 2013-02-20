#!/usr/bin/python2.7
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab


import sys, os
from setuptools import setup, find_packages

NAME = "router"

VERSION = "1.0"


DATAFILES = [
    (os.path.join(sys.prefix, 'libexec', 'pycopia'), glob("libexec/*")),
]


setup (name=NAME, version=VERSION,
    packages = find_packages("source"),
    package_dir = {"": "source"},
    test_suite = "test.RouterTests",
    data_files = DATAFILES,

    author = "Keith Dart",
    author_email = "keith@dartworks.biz",
    description = "Router appliance management and interface.",
    long_description = """Router appliance management and interface.
    """,
    license = "LGPL",
    keywords = "pycopia router",
    url = "http://www.pycopia.net/",
    dependency_links = [
            "http://www.pycopia.net/download/"
                ],
    #download_url = "ftp://ftp.pycopia.net/pub/python/%s-%s.tar.gz" % (NAME, VERSION),
    classifiers = ["Programming Language :: Python",
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   "Intended Audience :: Developers"],
)

