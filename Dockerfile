FROM python:3.10.13

WORKDIR /app
ARG TARGET_BRANCH
ENV DEPLOYMENT=local

SHELL ["/bin/bash", "-c"]

RUN cp /usr/share/zoneinfo/Asia/Tokyo /etc/localtime

RUN apt-get update && apt-get upgrade -y \
&& apt-get -y install git unzip libgl1-mesa-dev cron \
&& curl -LsSf https://astral.sh/uv/install.sh | sh \
&& source ${HOME}/.local/bin/env \
&& git clone https://github.com/toposoid/toposoid-contents-admin-web.git \
&& cd toposoid-contents-admin-web \
&& git fetch origin ${TARGET_BRANCH} \
&& git checkout ${TARGET_BRANCH} \
&& git pull \
&& sed s/__##GIT_BRANCH##__/${TARGET_BRANCH}/g pyproject.toml.template > pyproject.toml \
&& cd /tmp \
&& git clone https://github.com/toposoid/toposoid-pdf-analyzer.git \
&& cd toposoid-pdf-analyzer \
&& git checkout ${TARGET_BRANCH} \
&& sed s/__##GIT_BRANCH##__/${TARGET_BRANCH}/g pyproject.toml.template > pyproject.toml \
&& cd /app/toposoid-contents-admin-web \
&& uv sync \
&& uv add git+https://github.com/toposoid/toposoid-python-lib.git@${TARGET_BRANCH}#egg=ToposoidCommon \
&& uv add /tmp/toposoid-pdf-analyzer --editable


RUN echo "* * * * * root find /app/toposoid-contents-admin-web/contents/temporaryUse/* -name '*' -mmin +10 -delete" >> /etc/crontab \
&& sed -i -e '/pam_loginuid.so/s/^/#/' /etc/pam.d/cron

COPY ./docker-entrypoint.sh /app/
ENTRYPOINT ["/app/docker-entrypoint.sh"]
