#!/bin/bash
export LANG=en_US.UTF-8
export PYTHONPATH=.:"$PYTHONPATH"
python2.5 _alltests.py "$@"

