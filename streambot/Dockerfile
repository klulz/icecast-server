FROM rockylinux:9 AS mp3base
# provide LAME/madplay/taglib

RUN yum -y install epel-release dnf-plugins-core
RUN dnf config-manager --enable crb
RUN yum -y install libid3tag-devel createrepo ncurses-devel

# create package repo and install
WORKDIR /root
ADD pkg mp3pkg/
RUN ["createrepo", "/root/mp3pkg"]
RUN ["chmod", "-R", "o-w+r", "/root/mp3pkg"]
ADD mp3pkg.repo /etc/yum.repos.d/
RUN yum install -y --nobest libmad-devel lame lame-libs taglib taglib-devel lame-devel wget patch clang make libid3tag-devel \
  libxml2-devel libvorbis-devel flac libtool gettext-devel check-devel file wget git openssl-devel libzstd-devel  \
  sox
RUN rm -rf /etc/yum.repos.d/mp3pkg.repo /root/mp3pkg

# madplay

FROM mp3base AS madplay

ADD libid3tag-0.15.1b.tar.gz /home/streambot/tmp
RUN ["mv", "/home/streambot/tmp/libid3tag-0.15.1b", "/home/streambot/tmp/libid3tag"]
WORKDIR /home/streambot/tmp/libid3tag
RUN wget -O config.guess 'https://git.savannah.gnu.org/gitweb/?p=config.git;a=blob_plain;f=config.guess;hb=HEAD'
RUN wget -O config.sub 'https://git.savannah.gnu.org/gitweb/?p=config.git;a=blob_plain;f=config.sub;hb=HEAD'
RUN ["./configure"]
RUN ["make", "-j2"]
RUN ["make", "install"]

ADD madplay-0.15.2b.tar.gz /home/streambot/tmp
RUN ["mv", "/home/streambot/tmp/madplay-0.15.2b", "/home/streambot/tmp/madplay"]
WORKDIR /home/streambot/tmp/madplay
RUN wget -O config.guess 'https://git.savannah.gnu.org/gitweb/?p=config.git;a=blob_plain;f=config.guess;hb=HEAD'
RUN wget -O config.sub 'https://git.savannah.gnu.org/gitweb/?p=config.git;a=blob_plain;f=config.sub;hb=HEAD'
RUN ["./configure"]
RUN ["make", "-j2"]
RUN ["make", "install"]

###

FROM madplay AS ezstream
# provide ezstream

RUN useradd -m streambot
WORKDIR /home/streambot/tmp
RUN chown -R streambot:streambot /home/streambot/tmp


# build libshout from source
RUN git clone --recurse-submodules --depth 1 https://github.com/xiph/Icecast-libshout.git
RUN cd Icecast-libshout && ./autogen.sh && ./configure && make -j2 && make install
RUN rm -rf Icecast-libshout

ENV EZSTREAM_REL=1_0_1
USER streambot
RUN wget -O ezstream.tar.gz https://github.com/xiph/ezstream/archive/release_${EZSTREAM_REL}.tar.gz
RUN ["tar", "-zxf", "ezstream.tar.gz"]
WORKDIR ezstream-release_1_0_1
#WORKDIR ezstream-release_1_0_2
#RUN wget -O ezstream-1.0.2.patch 'https://gitlab.xiph.org/xiph/ezstream/uploads/ba768fa1349c65b60affd496cf4282ed/ezstream-1.0.2.patch'
#RUN patch -p1 < ezstream-1.0.2.patch
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
RUN tar xzf Python-3.8.2.tgz && cd Python-3.8.2 && ./configure --enable-optimizations
RUN cd Python-3.8.2 && make
RUN cd Python-3.8.2 && make install
RUN yum install -y pipx
RUN chown -R streambot /home/streambot

USER streambot
WORKDIR /home/streambot

RUN mkdir -p $HOME/.local/bin
RUN pipx ensurepath
RUN pipx install poetry

# python deps
ADD pyproject.toml poetry.lock  ./
RUN /home/streambot/.local/bin/poetry install --no-dev

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
