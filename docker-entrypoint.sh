#!/bin/bash
cron -f && tail -f /dev/null &
cd /app/toposoid-contents-admin-web
uvicorn api:app --reload --host 0.0.0.0 --port 9012
