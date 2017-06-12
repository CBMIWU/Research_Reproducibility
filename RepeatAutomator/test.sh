#!/usr/bin/env bash
set -e

# Download NLTK resources
python -m nltk.downloader -d /tmp/nltk_data all
export NLTK_DATA=/tmp/nltk_data

# Compile Python files
python -m compileall .

# Run tests
if [[ -n "$CI" ]]; then
  echo "Running tests..."
  # Filter API key out of logs
  python objects/test.py 2>&1 | grep -vP "([A-Z]|[0-9]){32}"
  echo $?
else
  python objects/test.py
fi
