FROM python:3.10.13

WORKDIR /app
ARG TARGET_BRANCH
ARG GIT_TOKEN
ENV DEPLOYMENT=local

RUN cp /usr/share/zoneinfo/Asia/Tokyo /etc/localtime

RUN apt-get update && apt-get upgrade -y \
&& apt-get -y install git libgl1-mesa-dev cron \
&& git clone https://github.com/toposoid/toposoid-contents-admin-web.git \
&& cd toposoid-contents-admin-web \
&& git fetch origin ${TARGET_BRANCH} \
&& git checkout ${TARGET_BRANCH} \
&& sed -i s/__##GIT_TOKEN##__/${GIT_TOKEN}/g requirements.txt \
&& pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt \
&& rm -f requirements.txt

RUN echo "* * * * * root find /app/toposoid-contents-admin-web/contents/temporaryUse/* -name '*' -mmin +10 -delete" >> /etc/crontab \
&& sed -i -e '/pam_loginuid.so/s/^/#/' /etc/pam.d/cron

COPY ./docker-entrypoint.sh /app/
ENTRYPOINT ["/app/docker-entrypoint.sh"]
