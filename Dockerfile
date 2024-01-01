FROM python:3.9

WORKDIR /app
ARG TARGET_BRANCH
ENV DEPLOYMENT=local

RUN apt-get update && apt-get upgrade -y \
&& apt-get -y install git libgl1-mesa-dev cron \
&& git clone https://github.com/toposoid/toposoid-contents-admin-web.git \
&& cd toposoid-contents-admin-web \
&& git fetch origin ${TARGET_BRANCH} \
&& git checkout ${TARGET_BRANCH} \
&& pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt

COPY cron-toposoid-contents-admin-web /etc/cron.d/
RUN chmod 644 /etc/cron.d/cron-toposoid-contents-admin-web \
&& sed -i -e '/pam_loginuid.so/s/^/#/' /etc/pam.d/cron

COPY ./docker-entrypoint.sh /app/
ENTRYPOINT ["/app/docker-entrypoint.sh"]
