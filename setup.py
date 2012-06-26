#!/usr/bin/env
from distutils.core import setup

setup(
    name="pongo",
    author="Matias Surdi",
    author_email="matias@youzee.com",
    description="Postfix tcp_table interface for mongo",
    version="0.3",
    packages=["pongo","pongo.bin"],
    scripts=["pongo/bin/pongoserver"]
    )
