#!/usr/bin/env zsh

PYTHONPATH=$(readlink -f $0 | xargs dirname):$PYTHONPATH
