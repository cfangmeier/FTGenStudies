#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
from ft_tools.results import Run

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Unpacks result archives from a HTCondor run")
    add = parser.add_argument
    add('run_name')
    args = parser.parse_args()
    run = Run(args.run_name)
    run.unpack_tasks()

