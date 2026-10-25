#!/bin/sh
cd "$(dirname "$0")" || exit 1
printf '\nOpen http://127.0.0.1:8765 in Chrome or Edge once the server starts.\n'
python3 local_server.py
