#!/usr/bin/env python3

import os

# Get the API key and URL from the environment
config = {
    "api_token": os.environ.get("REDCAP_API_KEY"),
    "api_url": os.environ.get("REDCAP_API_URL")
}

if os.environ.get("REDCAP_API_KEY") is None or os.environ.get("REDCAP_API_URL") is None:
    print("WARNING: API key or API URL not found")
