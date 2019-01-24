#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import sys
from os import walk, chmod, mkdir
from os.path import isfile, isdir, expanduser, join, realpath
import argparse
from shutil import rmtree
from pathos.multiprocessing import Pool
from itertools import product
import dill
import tqdm

from ft_tools.utils import pdgIds, info, info2, get_yes_no, sh
import ft_tools.mg as mg

NO_PROMPT = False
DRYRUN = False
THE_MG = 'MG5_aMC'
RUN_NAME = "procs"
BASE_DIR = "./"
RUN_DIR = join(BASE_DIR, 'runs', RUN_NAME)

def main(tasks, mg_version):
    global THE_MG
    install_ok, THE_MG = mg.check_install(mg_version)
    if not install_ok:
        mg.install_version(mg_version)

    if tasks:
        info('Generating the following processes:')
        for i, cfg in enumerate(tasks):
            info2('{:2d})  {:20s}  @ {:5.2f}TeV with '.format(i+1, cfg.proc_name, cfg.com_energy) +
                  ', '.join('{}={}'.format(k, v) for k, v in cfg._setup.items() if k not in ('proc_name', 'com_energy')))
        if not get_yes_no('Proceed?', True, no_prompt=NO_PROMPT):
            return
        if HTCONDOR:
            if not isfile(THE_MG+'.tar.gz'):
                sh('tar', ['-czf', THE_MG+'.tar.gz', THE_MG])
            if not isdir(join(RUN_DIR, 'condor_logs')):
                mkdir(join(RUN_DIR, 'condor_logs'))
            for task in tqdm.tqdm(tasks, total=len(tasks)):
                gen_proc(task)
        else:
            # pool = Pool(3)
            # for _ in tqdm.tqdm(pool.imap_unordered(gen_proc, tasks), total=len(tasks)):
            #     pass
            for _ in tqdm.tqdm((gen_proc(task) for task in tasks), total=len(tasks)):
                pass

    if args.publish:
        pubdir = join(expanduser('~'), 'public_html')
        info('Copying output to ' + pubdir)
        procdir = join(pubdir, args.run_name)

        sh('rm', ['-rf', procdir])
        sh('cp', ['-r', args.run_name, pubdir])

        info('Fixing permissions...')

        chmod(procdir, 0o755)
        for cwd, dirs, files in walk(procdir):
            for dir_ in dirs:
                path = join(cwd, dir_)
                try:
                    chmod(path, 0o755)
                except OSError:
                    pass
            for file_ in files:
                path = join(cwd, file_)
                try:
                    chmod(path, 0o744)
                except OSError:
                    pass
        info('Done!')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run MG for TTTT Studies")
    add = parser.add_argument
    add('run_name')

    tasks = []
    if args.proc:
        if not isdir(join(BASE_DIR, 'runs')):
            mkdir(join(BASE_DIR, 'runs'))
        if isdir(RUN_DIR):
            if args.nokeep or get_yes_no(RUN_NAME+' exists. Remove old results?', no_prompt=NO_PROMPT):
                rmtree(RUN_DIR, ignore_errors=True)
                mkdir(RUN_DIR)
        else:
            mkdir(RUN_DIR)

        # NOTE: Update logic here to add additional configuration
        mass_labels = [x[0] for x in args.mass]
        mass_sets = [list(zip(mass_labels, x)) for x in product(*[m[1] for m in args.mass])]

        param_labels = [x[0:2] for x in args.param]
        param_sets = [list(zip(param_labels, x)) for x in product(*[m[2] for m in args.param])]

        # print(param_labels)
        # print(param_sets)
        # sys.exit(0)

        for com_energy, mass_set, param_set in product(args.comenergies, mass_sets, param_sets):
            tasks.extend(Task(model=args.model,
                              proc_name=proc_name,
                              proc_order=proc_order,
                              com_energy=com_energy,
                              masses=mass_set,
                              params=param_set)
                         for proc_name, proc_order in args.proc)

        all_tasks = {task.job_name: task for task in tasks}
        dill_filename = join(RUN_DIR, 'batch.dill')
        if not args.nokeep and isfile(dill_filename):
            with open(dill_filename, 'rb') as f:
                all_tasks.update(dill.load(f))

        with open(dill_filename, 'wb') as f:
            dill.dump(all_tasks, f)

    main(tasks, args.mg)
