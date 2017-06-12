#!/usr/bin/env python3
# The MIT License (MIT)

# Copyright (c) 2014 Dean Malmgren

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

from __future__ import print_function, unicode_literals
import subprocess

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

def pdftotext(filename):
    """Extract text from pdfs using the pdftotext command line utility."""
    # run a subprocess and put the stdout and stderr on the pipe object
    pipe = subprocess.Popen(
        ['pdftotext', filename, '-'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )

    # pipe.wait() ends up hanging on large files. using
    # pipe.communicate appears to avoid this issue
    stdout, _ = pipe.communicate()

    # if pipe is busted, raise an error (unlike Fabric)
    if pipe.returncode != 0:
        print("FATAL: Error from pipe!")

    # print(stdout)
    return stdout
