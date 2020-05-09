FROM centos:7 AS mp3base
# provide LAME/madplay/taglib

# RUN yum -y install epel-release
RUN yum -y install libid3tag-devel createrepo ncurses-devel

# create package repo and install
WORKDIR /root
ADD pkg mp3pkg/
RUN ["createrepo", "/root/mp3pkg"]
RUN ["chmod", "-R", "o-w+r", "/root/mp3pkg"]
ADD mp3pkg.repo /etc/yum.repos.d/
RUN yum install -y libmad madplay lame lame-devel lame-libs taglib taglib-devel
RUN rm -rf /etc/yum.repos.d/mp3pkg.repo /root/mp3pkg

###

FROM mp3base AS ezstream
# provide ezstream

RUN useradd -m streambot
WORKDIR /home/streambot/tmp
RUN chown -R streambot:streambot /home/streambot/tmp

# deps
RUN yum -y install clang make libxml2-devel libvorbis-devel wget libid3tag-devel flac libtool gettext-devel check-devel file wget git openssl-devel

# build libshout from source
RUN git clone --recurse-submodules --depth 1 https://github.com/xiph/Icecast-libshout.git
RUN cd Icecast-libshout && ./autogen.sh && ./configure && make -j2 && make install
RUN rm -rf Icecast-libshout

ENV EZSTREAM_REL=1_0_1
USER streambot
RUN wget -O ezstream.tar.gz https://github.com/xiph/ezstream/archive/release_${EZSTREAM_REL}.tar.gz
RUN ["tar", "-zxf", "ezstream.tar.gz"]
WORKDIR ezstream-release_1_0_1
RUN ["./autogen.sh"]
RUN PKG_CONFIG_PATH=/usr/local/lib/pkgconfig ./configure
RUN ["make", "-j2"]
USER root
RUN ["make", "install"]

###

FROM ezstream AS streambot-klulz
# provide ice3 S3 streambot script

# deps
WORKDIR /home/streambot/tmp
RUN wget https://www.python.org/ftp/python/3.8.2/Python-3.8.2.tgz
RUN tar xzf Python-3.8.2.tgz && cd Python-3.8.2 && ./configure --enable-optimizations && make altinstall

USER streambot
WORKDIR /home/streambot
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python

# python deps
ADD pyproject.toml poetry.lock  ./
RUN /home/streambot/.poetry/bin/poetry install --no-dev

# cleanup
USER root
RUN rm -rf /home/streambot/tmp
RUN chown -R streambot /home/streambot
RUN yum clean all && \
  rm -rf /var/cache/yum

# configuration
WORKDIR /home/streambot
ADD ezstream.xml playlist.sh s3playlist.py update-config.sh ./
RUN chmod og-rw ezstream.xml playlist.sh s3playlist.py
USER root
RUN chown -R streambot /home/streambot/*
USER streambot

CMD ./update-config.sh && echo "Beginning stream..." && \
  while [ true ]; do ezstream -vv -c ezstream.xml; sleep 3; done
