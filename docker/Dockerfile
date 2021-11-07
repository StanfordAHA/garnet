FROM ubuntu:latest

LABEL description="A docker image for Garnet test flow"
LABEL maintainer=keyi@cs.stanford.edu

ENV DEBIAN_FRONTEND="noninteractive"

RUN  apt-get update \
  && apt-get install -y --no-install-recommends git gcc-9 g++-9 python3 \
     python3-pip verilator cmake clang-8 build-essential curl wget  \
     libigraph0-dev zlib1g-dev libpng-dev libjpeg-dev python3-dev \
     python3-setuptools make python3-wheel libncurses5-dev \
     csh imagemagick libgmp-dev libmpfr-dev libmpc-dev file default-jre \
  && ln -fs /usr/share/zoneinfo/America/Los_Angeles /etc/localtime \
  && dpkg-reconfigure --frontend noninteractive tzdata \
  && apt-get clean

RUN  ln -s /usr/bin/python3 /usr/bin/python
