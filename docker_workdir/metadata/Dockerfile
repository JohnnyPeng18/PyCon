FROM python:3.10
RUN pip install --no-cache-dir pipdeptree
RUN pip install --no-cache-dir graphviz
RUN sed -i 's/jessie/buster/g' /etc/apt/sources.list
RUN apt update
RUN apt install --force-yes -y jq
