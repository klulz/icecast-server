# Quickstart
1. `cp sample/* ./`
2. Edit `icecast.xml` and `streambot.env`
3. `docker-compose up`

# Description
An internet radio station in a box.

A well-functioning internet radio station consists of a few things:
* A bot that is streaming a collection of audio files on shuffle
* Multiple mountpoints for streamers to go live and do sound check
* High availability

# KLULZ-Icecast
Based on an [old e-radio station](https://www.reddit.com/r/internetcollection/comments/60do6w/klulz_troll_radio/) but with modernized software and easily deployed as containers.

There are two containers: `icecast` and `streambot`.


## Icecast
[Icecast2](https://icecast.org/). A HTTP streaming audio server. Used for MP3 over HTTP ("Shoutcast"). Listens on port 8000.

You should edit the sample `icecast.xml` file and configure mountpoints and passwords.

Stream sources such as streambot and DJs connect to different mountpoints with differing priority levels. When a source connects to a mountpoint of higher priority than what is currently playing, listeners will be moved to the new mountpoint.

Typical setup:
* `/error.mp3` - An audio file that is played when everything is offline (something broke)
* `/zsoundcheck.mp3` - Lowest priority, listeners should never hear, just for testing sources
* `/streambot.mp3` - Default shuffle playlist, provided by streambot
* `/dj1.mp3` - Current streamer can connect here
* `/dj2.mp3` - Higher-priority streamer can connect here


## Streambot
Fetches random audio files from a S3 bucket (+ optional prefix) and streams them to icecast using [ezstream](https://github.com/xiph/ezstream).

Can post messages on SQS or SNS with now-playing metadata (track name, album, etc).

Configure it by editing `streambot.env`:
```
STREAM_HOST=icecast
STREAM_PORT=8000
STREAM_MOUNTPOINT=/streambot.mp3
STREAM_USER=streambot
STREAM_PASS=hackme
STREAM_NAME=Testing streambot
BUCKET_NAME=my-tunes
S3_PREFIX=on-deck
INFO_URL=https://radio.llolo.lol
GENRE=Dubtechno
DESCRIPTION=Made with KLULZ-Icecast
SQS_URL=https://sqs.us-west-2.amazonaws.com/123456709/klulz-nowplaying
SNS_ARN=arn:aws:sns:us-west-2:123456709:klulz-nowplaying

# if testing locally, you can provide AWS credentials
AWS_ACCESS_KEY_ID=AKIA.....
AWS_SECRET_ACCESS_KEY=.....
AWS_DEFAULT_REGION=us-west-2
```


### Configuration file documentation:
* [Icecast](http://owl.homeip.net/manuals/services/icecast/icecast2_config_file.html)
* [Madplay](https://www.systutorials.com/docs/linux/man/1-madplay/)
* [LAME](https://svn.code.sf.net/p/lame/svn/trunk/lame/USAGE)

# Contact
There's a demo of this running at [radio.llolo.lol](https://radio.llolo.lol), listen [here](https://radio.llolo.lol/listen.mp3.m3u).

Contact radio@llolo.lol if you'd like to participate.
