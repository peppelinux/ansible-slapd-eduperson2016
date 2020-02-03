# DOCKER-VERSION 17.10.0-ce
FROM buster:slim
MAINTAINER Giuseppe De Marco <giuseppe.demarco@unical.it>

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN apt-get update \
    && apt-get install -y python3-dev python3-setuptools python3-pip \
                          easy-rsa expect-dev git ldap-utils

# install dependencies
RUN pip install --upgrade pip ansible

# generate chosen locale
RUN sed -i 's/# it_IT.UTF-8 UTF-8/it_IT.UTF-8 UTF-8/' /etc/locale.gen
RUN locale-gen it_IT.UTF-8
# set system-wide locale settings
ENV LANG it_IT.UTF-8
ENV LANGUAGE it_IT
ENV LC_ALL it_IT.UTF-8

COPY . /ansible-slapd-eduperson2016
WORKDIR /ansible-slapd-eduperson2016

## Add the wait script to the image
ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.7.2/wait /wait
RUN chmod +x /wait

# Create certificates
RUN bash make_CA.production.sh

# check with
# docker inspect --format='{{json .State.Health}}' slapd_master
# HEALTHCHECK --interval=3s --timeout=2s --retries=1 CMD curl --fail http://localhost:8000/ || exit 1

RUN ansible-playbook -i "localhost," -c local playbook.production.yml
EXPOSE 636
EXPOSE 389
