#!/usr/bin/env python2
# -*- coding: utf-8 -*- 
from __future__ import print_function
import argparse
from glob import glob
from os import rename, walk, chmod
from os.path import isfile, isdir, expanduser, join
from subprocess import call, STDOUT
from multiprocessing import Pool
import tqdm
import re


class C:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def info(text, **kwargs):
    print(C.HEADER+text+C.ENDC, **kwargs)

def info2(text, **kwargs):
    print(C.OKGREEN+text+C.ENDC, **kwargs)

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
    'ttw_nlo': 'generate p p > t t~ w+ [QCD]',
    'ttz_lo': 'generate p p > t t~ z',
    'ttz_nlo': 'generate p p > t t~ z [QCD]',
    'tth_lo': 'generate p p > t t~ h',
    'tth_nlo': 'generate p p > t t~ h [QCD]',
    'tttt_lo': 'generate p p > t t~ t t~',
    'tttt_nlo1': 'generate p p > t t~ t t~ [QCD]',
    'tttt_nlo2': 'generate p p > t t~ t t~ QED=99',
    'tttt_nlo3': 'generate p p > t t~ t t~ QCD=0',
}


def sh(cmd, args, output=None):
    if output is not None:
        retval = call([cmd] + list(args), stdout=output, stderr=STDOUT)
    else:
        retval = call([cmd] + list(args))
    if retval:
        raise RuntimeError('command failed to run(' + str(retval) + '): ' + str(cmd) + ' ' + str(args))

def install_mg5(use_beta=False):
    info('Installing Madgraph')
    if use_beta:
        version = 'v3.0.0.beta'
        dir_ = 'v3_0_0'
    else:
        version = 'v2.6.3.2'
        dir_ = 'v2_6_3_2'
    url = "https://launchpad.net/mg5amcnlo/2.0/2.6.x/+download/MG5_aMC_{}.tar.gz".format(version)
    sh('wget', [url, '--output-document=MG5_aMC.tar.gz'])
    sh('tar', ['-xf', 'MG5_aMC.tar.gz'])
    sh('rm', ['MG5_aMC.tar.gz'])
    sh('mv', ['MG5_aMC_'+dir_, 'MG5_aMC'])
    sh('sed', ['-e', 's/# automatic_html_opening = .*/automatic_html_opening = False/', '-i' , 'MG5_aMC/input/mg5_configuration.txt'])
    info('Done!')



def dir_name(proc_name, beamenergy):
    if type(beamenergy) is str:
        beamenergy = float(beamenergy)
    return '{proc_name}_{beamenergy:.1f}TeV'.format(proc_name=proc_name, beamenergy=beamenergy)

def gen_proc(args):
    proc_name, beamenergy = args
    log = open(dir_name(proc_name, beamenergy)+'.log', 'w')
    dir_name_ = dir_name(proc_name, beamenergy)
    cproc = template.format(proc=procs[proc_name], dir_name=dir_name_)
    fname = proc_name+'.dat'
    with open(fname, 'w') as f:
        f.write(cproc)
    sh('mkdir', ['-p', 'procs'], output=log)
    sh('rm', ['-rf', 'procs/{dir_name}'.format(dir_name=dir_name_)], output=log)
    sh('./MG5_aMC/bin/mg5_aMC', ['-f', fname], output=log)
    sh('sed', ['-e', 's/.* = ebeam1/      {energy:.1f}  = ebeam1/'.format(energy=500*beamenergy), '-i',
       'procs/{dir_name}/Cards/run_card.dat'.format(dir_name=dir_name_)], output=log)
    sh('sed', ['-e', 's/.* = ebeam2/      {energy:.1f}  = ebeam2/'.format(energy=500*beamenergy), '-i',
       'procs/{dir_name}/Cards/run_card.dat'.format(dir_name=dir_name_)], output=log)
    sh('./procs/{dir_name}/bin/generate_events'.format(dir_name=dir_name_), ['-f'], output=log)
    log.close()


def tables():
    from bs4 import BeautifulSoup as Soup
    info("Generating tables")
    class Row:
        def __init__(self, proc, beamenergy):
            self.proc = proc
            self.beamenergy = beamenergy
            self.crossx = 'N/A'
            self.stat_err = 0
            self.syst_err = 0
            self.note = ""
    rows = []
    for fname in glob("procs/*"):
        proc, beamenergy = re.findall(r"procs/([a-zA-Z_0-9]+)_([0-9\.]+)TeV", fname)[0]
        row = Row(proc, beamenergy)
        try:
            with open(join(fname, 'crossx.html')) as f:
                soup = Soup(f, 'html5lib')
            text_raw = soup.select("tr")[1].select("td")[3].get_text()
            crossx, stat_err = re.findall(r"([\.0-9e\-]+) . ([\.0-9e\-]+)", text_raw, re.UNICODE)[0]
            row.crossx = crossx
            row.stat_err = stat_err

            # Since MG is dumb, LO systematics are stored separately from NLO systematics
            # ¯\_(ツ)_/¯
            if "nlo" in proc:
                # get from NLO place: {proc}/Events/run_01/summary.txt
                pass
            else:
                # get from LO place: bottom of {proc}/Events/run_01/parton_systematics.log
                pass

        except IOError as e:
            row.note = "crossx.html not found"
        except IndexError as e:
            row.note = "couldn't extract xsection from crossx.html"

        rows.append(row)

    rows.sort(key=lambda r: r.beamenergy)
    rows.sort(key=lambda r: r.proc)
    rows_html = [("<tr><td><a href=\"{}\">{}</a></td><td>{}</td>"
                  "<td>{}</td><td>{}</td><td>{}</td></tr>").format(dir_name(row.proc, row.beamenergy),
                                                                   row.proc, row.beamenergy,
                                                                   row.crossx, procs[row.proc], row.note) for row in rows]
    header = "<tr><th>Process</th><th>Beam Energy</th><th>Cross-Section (pb)</th><th>Command</th><th>Note</th></tr>"
    table = "<table>{}<tbody>{}</tbody><table>".format(header, '\n'.join(rows_html))

    with open("summary.html", "w") as f:
        f.write(table)

    info("Done!")

def main(args):
    if not isdir('MG5_aMC'):
        install_mg5()
    tasks = []
    if args.all:
        for beamenergy in args.beamenergies:
            tasks.extend((proc_name, beamenergy) for proc_name in procs if not isdir(dir_name(proc_name, beamenergy)))
    elif args.processes:
        for beamenergy in args.beamenergies:
            tasks.extend((proc_name, beamenergy) for proc_name in args.processes if not isdir(dir_name(proc_name, beamenergy)))
    if tasks:
        pool = Pool(5)
        info('Generating the following processes:')
        for i, (proc_name, beamenergy) in enumerate(tasks):
            info2("{:2d})  {:20s}  @ {:5.2f}TeV".format(i+1, proc_name, beamenergy))
        for _ in tqdm.tqdm(pool.imap_unordered(gen_proc, tasks), total=len(tasks)):
            pass

    if args.tables:
        tables()

    if args.publish:
        info('Copying output to ~/public_html/procs')
        pubdir = join(expanduser('~'), 'public_html')
        procdir = join(pubdir, 'procs')

        sh('rm', ['-rf', procdir])
        sh('cp', ['-r', 'procs/', pubdir])

        info('Fixing permissions...')
        if isfile("summary.html"):
            sh('cp', ['summary.html', procdir])
            chmod(join(procdir, "summary.html"), 0744)

        chmod(procdir, 0755)
        for cwd, dirs, files in walk(procdir):
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
        info('Done!')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run MG for TTTT Studies")
    add = parser.add_argument
    add('-p', '--processes', nargs='+')
    add('--all', action='store_true')
    add('--publish', action='store_true')
    add('--tables', action='store_true')
    add('--beamenergies', default=[13.0], type=float, nargs='+')

    args = parser.parse_args()
    main(args)
