##### ICECAST2
FROM ubuntu:noble AS icecast-klulz

MAINTAINER Mischa Spiegelmock "me@mish.dev"

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -qq -y update && \
  apt-get -qq -y install icecast2 && \
  apt-get clean

ADD start.sh /start-icecast2.sh
ADD error.mp3 /usr/share/icecast2/web/error.mp3
ADD etc-icecast2 /etc/icecast2
RUN chown -R icecast2 /etc/icecast2 /start-icecast2.sh

USER icecast2
CMD ["/start-icecast2.sh"]
