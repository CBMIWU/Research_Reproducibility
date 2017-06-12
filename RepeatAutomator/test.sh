#!/usr/bin/env bash

export NLTK_DATA=/tmp/nltk_data

python -m compileall .

if [[ -n "$CI" ]]; then
  python objects/test.py 2&> /dev/null
else
  python objects/test.py
fi
