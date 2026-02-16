#!/bin/bash
#chmod 644 /etc/cron.d/cron-toposoid-contents-admin-web
#sed -i -e '/pam_loginuid.so/s/^/#/' /etc/pam.d/cron
cron -f && touch /etc/crontab && tail -f /dev/null &
cd /app/toposoid-contents-admin-web
source /root/.local/bin/env
uv run uvicorn api:app --reload --host 0.0.0.0 --port 9012
