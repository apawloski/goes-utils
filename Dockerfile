from ubuntu:20.04

RUN apt-get update --fix-missing
RUN DEBIAN_FRONTEND="noninteractive" apt-get install -y python3-pip ffmpeg imagemagick

RUN mkdir /goes
WORKDIR /goes
ADD requirements.txt /goes
RUN pip3 install -r requirements.txt
ADD commonlib /goes/commonlib
ADD video_generator.py /goes



