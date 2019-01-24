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

CARD_TEMPLATE = '''
set run_mode {run_mode}
set nb_core {nb_core}
import {model_type} {model}
define p = p b b~
define j = p
{proc}
output {output}
launch
set run_card ebeam1 {beamenergy}
set run_card ebeam2 {beamenergy}
set run_card nevents {nevent}
'''

CONDOR_TEMPLATE = '''
Universe      = Docker
+WantDocker   = True
docker_image  = "opensciencegrid/osgvo-el6"
executable    = {job_name}.sh
error         = condor_logs/{job_name}.err
output        = condor_logs/{job_name}.out
log           = condor_logs/condor.log
requirements  = (TARGET.Machine != "t3.unl.edu")
RequestMemory = 3500

should_transfer_files = YES
when_to_transfer_output = ON_EXIT
transfer_input_files = {job_name}.dat,{mg_path}

queue
'''

CONDOR_EXE_TEMPLATE = '''\
#!/usr/bin/env bash

cmshome="/cvmfs/cms.cern.ch/slc6_amd64_gcc530/cms/cmssw/CMSSW_9_2_8/src/"

echo "starting run. Current time: " $(date)
echo "running @ " $(pwd) "in " $(hostname)
echo "Initial Directory Contents:"
ls -la

echo "Setting up environment"
source /cvmfs/cms.cern.ch/cmsset_default.sh
cd $cmshome
eval `scramv1 runtime -sh`
cd -

echo "Done. Listing env"
env

echo "Unpacking job content"
tar -xzf {the_mg}.tar.gz
rm {the_mg}.tar.gz
echo "Finished unpacking"
echo "Current Directory Contents:"
ls -la

echo "Starting Madgraph"
./{the_mg}/bin/mg5_aMC -f {job_name}.dat
echo "Madgraph finished"
echo "Current Directory Contents:"
ls -la

echo "Packing up Results"
tar -czf {job_name}.tar.gz {job_name}/
echo "Finished!"
'''


PROCS = {
    # SM processes
    'sm': {
        'tt': 'generate p p > t t~',
        'ttw': ('generate p p > t t~ w+',
                'add process p p > t t~ w-'),
        'ttz': 'generate p p > t t~ z',
        'tth': 'generate p p > t t~ h',

        'tttt': 'generate p p > t t~ t t~',
        'gg_to_tttt': 'generate g g > t t~ t t~',
        'tth_hTobb': 'generate p p > t t~ h, h > b b~',
    },
    # 2HDM processes
    '2HDM': {
        'tth1': 'generate p p > t t~ h1',
        'tth2': 'generate p p > t t~ h2',
        'tth3': 'generate p p > t t~ h3',

        'tthxbb': ('generate p p > t t~ h1, h1 > b b~',
                   'add process p p > t t~ h2, h2 > b b~'),
    },
    # s4top_v4 processes
    "s4top_v4": {
        'tth' : 'generate p p > t t~ h',
        'tth2': 'generate p p > t t~ h2',
        'tth3': 'generate p p > t t~ h3',

        'tth_hTott'  : 'generate p p > t t~ h, h > t t~',
        'tth2_h2Tott': 'generate p p > t t~ h2, h2 > t t~',
        'tth3_h3Tott': 'generate p p > t t~ h3, h3 > t t~',
    },
    # 2HDMtII_NLO processes
    "2HDMtII_NLO": {
        'tth1': 'generate p p > t t~ h1',
        'tth2': 'generate p p > t t~ h2',
        'tth3': 'generate p p > t t~ h3',

        'tth1tt': 'generate p p > t t~ h1, h1 > t t~',
        'tth2tt': 'generate p p > t t~ h2, h2 > t t~',
        'tth3tt': 'generate p p > t t~ h3, h3 > t t~',
    },
    # Z-Prime Model
    "Zprime_UFO": {
        'tttt': 'generate p p > t t~ t t~',
    },
    # DM-Scalar
    "DMScalar": {
        'tt'          : 'generate p p > t t~',
        'ttchichi'    : 'generate p p > t t~ chi chi~',
        'ttchichiJets': ('generate p p > t t~ chi chi~',
                         'add process p p > t t~ chi chi~ j'),
    },
    # DM-PseudoScalar
    "DMPseudo": {
        'tt'          : 'generate p p > t t~',
        'ttchichi'    : 'generate p p > t t~ chi chi~',
        'ttchichiJets': ('generate p p > t t~ chi chi~',
                         'add process p p > t t~ chi chi~ j'),
    },
}

notes = {
    'tttt_lo': 'Four-top leading order, QCD diagrams only',
    'tttt_lo_only_qed': 'Four-top leading order, QED diagrams only',
    'tttt_lo_add_qed': 'Four-top leading order, QCD+QED diagrams',
    'tttt_nlo': 'Four-top next-to-leading order, QCD diagrams only',
}


def gen_proc(task):
    log = open(join(RUN_DIR, task.job_name) + '.log', 'w')
    model_type = "model"
    if task.model[-3:] == "_v4":
        model_type += "_v4"
    try:
        proc = PROCS[task.model][task.proc_name]
        if type(proc) is str:
            proc = [proc]
        proc = '\n'.join((proc_line + ' ' + task.proc_order) for proc_line in proc)
    except KeyError:
        print("Error: Unkown process '{}' for model '{}'".format(task.proc_name, task.model))
        return
    if HTCONDOR:
        output = task.job_name
    else:
        output = join(RUN_DIR, task.job_name)
    # run_mode = 0 if HTCONDOR else 2
    run_mode = 2
    cproc = CARD_TEMPLATE.format(proc=proc, output=output,
                                 model_type=model_type,
                                 model=task.model,
                                 beamenergy=500 * task.com_energy,
                                 run_mode=run_mode,
                                 nb_core=NCORE,
                                 nevent=NEVENT)
    for pName, set_mass in task.masses:
        pdg_id = pdgIds[pName]
        cproc += '\nset param_card mass {} {}'.format(pdg_id, set_mass)
    for (block, idx), value in task.params:
        cproc += '\nset param_card {} {} {}'.format(block, idx, value)
    fname = join(RUN_DIR, task.job_name + '.dat')
    with open(fname, 'w') as f:
        f.write(cproc)

    if HTCONDOR:
        # Need to
        #  1. zip up the card and MG directory to ship over to the worker node.
        #  2. Write a script to source the environment, unzip the directory, and execute madgraph
        with open(join(RUN_DIR, task.job_name+'.condor'), 'w') as f:
            mg_path = realpath(THE_MG+'.tar.gz')
            f.write(CONDOR_TEMPLATE.format(job_name=task.job_name, the_mg=THE_MG, mg_path=mg_path))
        with open(join(RUN_DIR, task.job_name+'.sh'), 'w') as f:
            f.write(CONDOR_EXE_TEMPLATE.format(job_name=task.job_name, the_mg=THE_MG))
        if not DRYRUN:
            sh('condor_submit', [task.job_name+'.condor'], cwd=RUN_DIR, output=log)

    elif not DRYRUN:
        log.write("Running Madgraph for process \"{}\" @ {:.1f}TeV\n".format(task.proc_name, task.com_energy))
        rmtree(join(RUN_DIR, task.job_name), ignore_errors=True)
        sh('./'+THE_MG+'/bin/mg5_aMC', ['-f', fname], output=log)
    log.close()


class Task(object):
    def __init__(self, **kwargs):
        legal_chars = ('abcdefghijklmnopqrstufwxyz'
                       'ABCDEFGHIJKLMNOPQRSTUFWXYZ'
                       '0123456789_-.')

        self._setup = kwargs
        job_name = '_'.join(str(kwargs[key]) for key in sorted(list(kwargs.keys())))
        job_name = job_name.replace('.', 'p')
        self.job_name = ''.join(l for l in job_name if l in legal_chars)
        for key, val in kwargs.items():
            setattr(self, key, val)


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
    add('--workin', default='./', help='Place to dump results from run')
    add('--publish', action='store_true')
    add('--nokeep', action='store_true')
    add('--noprompt', action='store_true')
    add('--dryrun', action='store_true', help="Don't invoke madgraph, just write out proc_cards.")
    add('--condor', action='store_true', help="Run jobs as HTCondor submissions")
    add('--comenergies', default=[13.0], type=float, nargs='+')
    add('--model', default='sm')
    add('--ncore', default=4)
    add('--nevent', default=1000)
    add('--mg', default='2_6_4', help='version of madgraph to utilize')
    add('--mgversions', action='store_true', help='List available MG versions and quit')

    def mass(arg_str):
        label, masses = arg_str.split(':')
        return label, [float(m) for m in masses.split(',')]
    add('--mass', action='append', default=[], type=mass, metavar='NAME:MASS[,MASS,MASS,...]')

    def param(arg_str):
        block, idx, values = arg_str.split(':')
        return block, int(idx), [float(v) for v in values.split(',')]
    add('--param', action='append', default=[], type=param, metavar='BLOCK:IDX:VAL[,VAL,VAL,...]')

    def process(arg_str):
        return arg_str.split(':') if ':' in arg_str else (arg_str, '')
    add('--proc', action='append', default=[], type=process, metavar='PROCNAME:(ORDER)')

    args = parser.parse_args()

    if args.mgversions:
        for i, v in enumerate(sorted(mg.get_versions())):
            print('{}) {}'.format(i, v))
        sys.exit(0)

    NO_PROMPT = args.noprompt
    DRYRUN = args.dryrun
    HTCONDOR = args.condor
    NCORE = args.ncore
    NEVENT = args.nevent
    RUN_NAME = args.run_name[args.run_name.rfind('/')+1:]  # strip directory if supplied
    BASE_DIR = args.workin
    RUN_DIR = join(BASE_DIR, 'runs', RUN_NAME)

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
