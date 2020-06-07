#!/usr/bin/env python3
"""S3 bucket playlist generator."""

import logging
import os
import random
import re
import sys
import time
import json
from configparser import ConfigParser

import boto3

import eyed3

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class S3Playlister:
    """Grabs files from the specified bucket and plays a random one."""

    playlist_cache_file: str
    storage_dir: str
    bucket_name: str
    s3_prefix: str
    config: dict

    def __init__(self):
        """Init."""
        self._s3 = None
        self.config = None
        self._read_config()

        self.bucket_name = self.config.get("streamer", "BUCKET_NAME")
        self.s3_prefix = self.config.get("streamer", "S3_PREFIX")
        if not self.bucket_name:
            print("BUCKET_NAME not configured")
            sys.exit(1)

        # create storage area
        from os.path import expanduser

        storage_dir = expanduser("~/s3playlist")
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
        self.storage_dir = storage_dir
        self.playlist_cache_file = os.path.join(self.storage_dir, "playlist_cache.txt")
        boto3.set_stream_logger("botocore", level=logging.WARN)
        boto3.set_stream_logger("s3transfer", level=logging.WARN)
        boto3.set_stream_logger(level=logging.WARN)

    def get_next_file(self):
        """Return next S3 file to play.

        May download the file.
        """
        self.clean_old_files()

        files = self.get_s3_files()
        keys = [f["Key"] for f in files]
        mp3keys = set([k for k in keys if self.is_key_playable(k)])
        if not mp3keys:
            self._fail("No files found in bucket {}".format(self.bucket_name))
        # pick random key, get file obj
        mp3key = random.sample(mp3keys, 1)[0]
        mp3keyobj = None
        # search and find the response obj
        for f in files:
            if f["Key"] == mp3key:
                mp3keyobj = f
                break
        else:
            self._fail("Couldn't locate file with key", mp3key)

        # do we have this file already?
        fpath = os.path.join(self.storage_dir, self._slugify(mp3key))
        if not os.path.exists(fpath):
            # make dirs
            dpath = os.path.dirname(fpath)
            if not os.path.exists(dpath):
                os.makedirs(dpath)
            # download it
            key = mp3keyobj["Key"]
            log.info(f"Fetching {key}")
            self.bucket().download_file(key, fpath)

        return fpath

    def _slugify(self, k):
        return k.replace(r"[\s\/]", "-")

    def _fail(self, *err):
        for e in err:
            log.error(e)
        sys.exit(1)

    def clean_old_files(self):
        """Delete files downloaded more than a while ago so we don't fill up the disk."""
        old_time_sec = 3600 * 2  # 2 hours ago == old

        now = time.time()
        path = self.storage_dir
        # https://stackoverflow.com/questions/12485666/python-deleting-all-files-in-a-folder-older-than-x-days
        for filename in os.listdir(path):
            fpath = os.path.join(path, filename)
            if os.path.getmtime(fpath) < now - old_time_sec and os.path.isfile(fpath):
                print(f"Cleaning up {fpath}")
                os.remove(fpath)

    def get_s3_files(self) -> list:
        """List the files in the bucket."""
        ret = []

        # check for cached s3 list
        if os.path.exists(self.playlist_cache_file):
            with open(self.playlist_cache_file) as fh:
                try:
                    return json.load(fh)
                except Exception as err:
                    log.exception(err)

        def get_more(tok=""):
            params = dict(Bucket=self.bucket_name)
            if tok:
                params["ContinuationToken"] = tok
            if self.s3_prefix:
                params["Prefix"] = self.s3_prefix
            return self.s3client().list_objects_v2(**params)

        log.info("Fetching list of files in S3...")
        res = get_more()
        ret.extend(res["Contents"])

        while res["IsTruncated"]:
            if "NextContinuationToken" in res:
                tok = res["NextContinuationToken"]
                res = get_more(tok)
                ret += res["Contents"]
            else:
                print("Failed to find NextContinuationToken")

        # remove stuff we don't care about
        for r in ret:
            for f in ("LastModified", "ETag", "StorageClass"):
                del r[f]

        # save s3 list response in cache
        with open(self.playlist_cache_file, "w") as fh:
            json.dump(ret, fh, ensure_ascii=False, indent=4)

        return ret

    def is_key_playable(self, s3key):
        """Return if the filename looks like a file we can play or not."""
        endings = [".mp3", ".wav", ".flac", ".ogg"]
        for end in endings:
            if s3key.endswith(end):
                return True
        return False

    def can_list_bucket(self):
        """Check if we can list the bucket."""
        # throws error if fails
        client = self.s3client()
        client.head_bucket(Bucket=self.bucket_name)

    def bucket(self):
        """Return boto3 S3 bucket object."""
        return boto3.resource("s3").Bucket(self.bucket_name)

    def s3client(self):
        """Get S3 client."""
        if self._s3 is not None:
            return self._s3
        self._s3 = boto3.client("s3")
        return self._s3

    def post_sns_track(self, filename, tag):
        """Post a message containing the track we're about to play."""
        arn = self.config.get("streamer", "SNS_ARN")
        if not arn:
            return
        # dumb. https://github.com/boto/boto3/issues/871
        region = re.search(r"arn:aws:sns:([\w-]+):", arn).group(1)
        sns = boto3.resource("sns", region_name=region)
        topic = sns.Topic(arn)

        # our message to deliver
        msg = {"FileName": {"StringValue": filename, "DataType": "String"}}
        if tag:
            msg["Artist"] = {"StringValue": tag.artist, "DataType": "String"}
            msg["Title"] = {"StringValue": tag.title, "DataType": "String"}
            msg["Album"] = {"StringValue": tag.album, "DataType": "String"}

        topic.publish(MessageAttributes=msg, Message="track_update")

    def post_sqs_track(self, filename, tag):
        """Post a message containing the track we're about to play."""
        url = self.config.get("streamer", "SQS_URL")
        if not url:
            return
        # dumb. https://github.com/boto/boto3/issues/871
        region = re.search(r"sqs\.([\w-]+)\.amazonaws\.com", url).group(1)
        sqs = boto3.resource("sqs", region_name=region)

        # our message to deliver
        msg = {"FileName": {"StringValue": filename, "DataType": "String"}}
        if tag:
            msg["Artist"] = {"StringValue": tag.artist, "DataType": "String"}
            msg["Title"] = {"StringValue": tag.title, "DataType": "String"}
            msg["Album"] = {"StringValue": tag.album, "DataType": "String"}

        queue = sqs.Queue(url)
        queue.send_message(MessageAttributes=msg, MessageBody="track_update")

    def _read_config(self):
        if self.config:
            return self.config
        config = ConfigParser()
        config.read("ice3.ini")
        sections = config.sections()
        if "streamer" not in sections:
            print("Failed to load config")
            sys.exit(1)
        self.config = config
        return config


if __name__ == "__main__":
    pl = S3Playlister()

    # pick next track
    file = pl.get_next_file()

    # track update
    track_info = eyed3.load(file)

    if track_info:
        pl.post_sqs_track(os.path.basename(file), track_info.tag)
        pl.post_sns_track(os.path.basename(file), track_info.tag)

    print(file)
