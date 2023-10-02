#!/bin/bash

cd /app/toposoid-contents-admin-web
uvicorn api:app --reload --host 0.0.0.0 --port 9012
