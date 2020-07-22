FROM fedora:33

RUN dnf -y update
RUN dnf -y install nginx
RUN dnf -y install nss_wrapper
RUN dnf -y install python3-pygithub

COPY github.conf /etc/nginx/conf.d/github.conf
COPY hosts.conf /etc/nginx/hosts.conf

COPY enarx-* /usr/local/bin/
COPY enarxbot.py /usr/local/lib/python3.8/site-packages/
