#!/bin/bash

# This is a wrapper around s3playlist.py

if [[ -z "${1}" ]]; then
    # get filename to play
    /usr/bin/env python3.8 /home/streambot/.poetry/bin/poetry run ./s3playlist.py
elif [[ x"${1}" -eq "xartist" ]]; then
    # return artist
    # not implemented...
    echo "not implemented" >2
elif [[ x"${1}" -eq "xtitle" ]]; then
    # return artist
    # not implemented...
    echo "not implemented" >2
else
    echo "No idea what you want from me"
fi
