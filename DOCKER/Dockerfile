FROM ubuntu
MAINTAINER Alex Walender


RUN apt-get update
RUN mkdir /BibiCreator
RUN mkdir /etc/bibicreator

COPY /BibiImageCreator /BibiCreator
COPY packer /BibiCreator

RUN apt-get install -y python3 python3-pip ansible
RUN pip3 install -r BibiCreator/requirements.txt

ENV USER=ubuntu
EXPOSE 5000
ENTRYPOINT python3 /BibiCreator/__init__.py
