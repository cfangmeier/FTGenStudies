#!/usr/bin/env python2
from __future__ import print_function
import argparse
from glob import glob
from os import rename, walk, chmod
from os.path import isfile, isdir, expanduser, join
from subprocess import call, STDOUT
from multiprocessing import Pool
import tqdm


class C:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

template = '''
define p = p b b~
define j = p
{proc}
output procs/{dir_name}/
'''

procs = {
    'tt_lo': 'generate p p > t t~',
    'tt_nlo': 'generate p p > t t~ [QCD]',
    'ttw_lo': 'generate p p > t t~ w+',
    'ttz_lo': 'generate p p > t t~ z',
    'tth_lo': 'generate p p > t t~ h',
    'tttt_lo': 'generate p p > t t~ t t~'
}


def sh(cmd, args, output=None):
    if output is not None:
        retval = call([cmd] + list(args), stdout=output, stderr=STDOUT)
    else:
        retval = call([cmd] + list(args))
    if retval:
        raise RuntimeError('command failed to run(' + str(retval) + '): ' + str(cmd) + ' ' + str(args))

def install_mg5():
    print(C.OKGREEN, 'Installing Madgraph', C.ENDC)
    sh('wget', ['http://launchpad.net/madgraph5/2.0/2.6.x/+download/MG5_aMC_v2.6.3.2.tar.gz'])
    sh('tar', ['-xf', 'MG5_aMC_v2.6.3.2.tar.gz'])
    sh('rm', ['MG5_aMC_v2.6.3.2.tar.gz'])
    sh('mv', ['MG5_aMC_v2_6_3_2', 'MG5_aMC'])
    sh('sed', ['-e', 's/# automatic_html_opening = .*/automatic_html_opening = False/', '-i' , 'MG5_aMC/input/mg5_configuration.txt'])
    print(C.OKGREEN, 'Done!', C.ENDC)

def gen_proc(args):
    proc_name, beamenergy = args
    dir_name = '{proc_name}_{beamenergy:.1f}TeV'.format(proc_name=proc_name, beamenergy=beamenergy)
    cproc = template.format(proc=procs[proc_name], dir_name=dir_name)
    fname = proc_name+'.dat'
    with open(fname, 'w') as f:
        f.write(cproc)
    log = open(proc_name+'.log', 'w')
    sh('rm', ['-rf', 'procs/{dir_name}'.format(dir_name=dir_name)], output=log)
    sh('./MG5_aMC/bin/mg5_aMC', ['-f', fname], output=log)
    sh('sed', ['-e', 's/.* = ebeam1/      {energy:.1f}  = ebeam1/'.format(energy=500*beamenergy), '-i',
       'procs/{proc_name}_{beamenergy:.1f}TeV/Cards/run_card.dat'.format(proc_name=proc_name, beamenergy=beamenergy)], output=log)
    sh('sed', ['-e', 's/.* = ebeam2/      {energy:.1f}  = ebeam2/'.format(energy=500*beamenergy), '-i',
       'procs/{proc_name}_{beamenergy:.1f}TeV/Cards/run_card.dat'.format(proc_name=proc_name, beamenergy=beamenergy)], output=log)
    sh('./procs/{dir_name}/bin/generate_events'.format(dir_name=dir_name), ['-f'], output=log)
    log.close()


def main(args):
    if not isdir('MG5_aMC'):
        install_mg5()
    if args.all:
        pool = Pool(5)
        tasks = [(proc_name, args.beamenergy) for proc_name in procs]
        for _ in tqdm.tqdm(pool.imap_unordered(gen_proc, tasks), total=len(tasks)):
            pass
    elif args.process:
        gen_proc((args.proc, args.beamenergy))

    if args.publish:
        pubdir = join(expanduser('~'), 'public_html')
        sh('rm', ['-rf', join(pubdir, 'procs')])
        sh('cp', ['-r', 'procs/', pubdir])

        chmod(join(pubdir, 'procs'), 0755)
        for cwd, dirs, files in walk(join(pubdir, 'procs')):
            for dir_ in dirs:
                path = join(cwd, dir_)
                try:
                    chmod(path, 0755)
                except OSError:
                    pass
            for file_ in files:
                path = join(cwd, file_)
                try:
                    chmod(path, 0744)
                except OSError:
                    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run MG for TTTT Studies")
    add = parser.add_argument
    add('--process')
    add('--all', action='store_true')
    add('--publish', action='store_true')
    add('--beamenergy', default=13, type=float)

    args = parser.parse_args()
    main(args)
