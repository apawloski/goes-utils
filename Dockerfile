from ubuntu:20.04

RUN apt-get update
RUN DEBIAN_FRONTEND="noninteractive" apt-get install -y python3-pip ffmpeg

RUN mkdir /goes
WORKDIR /goes
ADD requirements.txt /goes
ADD commonlib /goes
ADD video_generator.py /goes
ADD site_update.sh /goes

RUN pip3 install -r requirements.txt

