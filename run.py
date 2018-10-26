#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

from sys import version_info
PY3 = version_info.major == 3

import argparse
from glob import glob
from os import rename, walk, chmod, mkdir
from os.path import isfile, isdir, expanduser, join, split
from shutil import rmtree
from subprocess import call, STDOUT
from pathos.multiprocessing import Pool
from itertools import product
import json
import dill
import tqdm
import re

if not PY3:
    input = raw_input

from utils import FLT_RE

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

NO_PROMPT = False

def get_yes_no(prompt, default=False):
    if NO_PROMPT:
        return default
    if default:
        while True:
            info(prompt + ' (Y/n)')
            x = input().strip().lower()
            if x == 'n':
                return False
            elif x in ('', 'y'):
                return True
    else:
        while True:
            info(prompt + ' (y/N)')
            x = input().strip().lower()
            if x == 'y':
                return True
            elif x in ('', 'n'):
                return False

pdgIds = {
    'd ':  1,
    'u ':  2,
    's ':  3,
    'c ':  4,
    'b':   5,
    't':   6,
    'e':   11,
    've ': 12,
    'mu':  13,
    'vm ': 14,
    'ta':  15,
    'vt ': 16,
    'g':   21,
    'a':   22,
    'z':   23,
    'w':   24,
    'h':   25,
    'h1':  25,
    'h2':  35,
    'h3':  36,
    'hc':  37,
}

RUN_NAME = "procs"

TEMPLATE = '''
import {model_type} {model}
define p = p b b~
define j = p
{proc}
output {job_name}/{dir_name}/
launch
set run_card ebeam1 {beamenergy}
set run_card ebeam2 {beamenergy}
set run_card nevents 10000
set param_card yukawa 6 {yukawa}
'''

PROCS = {
    # SM processes
    'sm': {
        'tt_lo': 'generate p p > t t~',
        'tt_nlo': 'generate p p > t t~ [QCD]',
        'ttw_lo': ('generate p p > t t~ w+\n'
                   'add process p p > t t~ w-'),
        'ttw_nlo': ('generate p p > t t~ w+ [QCD]\n'
                    'add process p p > t t~ w- [QCD]'),
        'ttz_lo': 'generate p p > t t~ z',
        'ttz_nlo': 'generate p p > t t~ z [QCD]',
        'tth_lo': 'generate p p > t t~ h',
        'tth_nlo': 'generate p p > t t~ h [QCD]',

        'tttt_lo_only_qcd': 'generate p p > t t~ t t~ QCD=99 QED=0',
        'tttt_lo_only_qed': 'generate p p > t t~ t t~ QCD=0  QED=99',
        'tttt_lo_all':      'generate p p > t t~ t t~ QCD=99 QED=99',

        'gg_to_tttt_lo_only_qcd': 'generate g g > t t~ t t~ QCD=99 QED=0',
        'gg_to_tttt_lo_only_qed': 'generate g g > t t~ t t~ QCD=0  QED=99',
        'gg_to_tttt_lo_all':      'generate g g > t t~ t t~ QCD=99 QED=99',

        'tttt_nlo': 'generate p p > t t~ t t~ [QCD]',
        'tttt_nlo_add_qed': 'generate p p > t t~ t t~ QED=99 [QCD]',

        'tthbb_lo': 'generate p p > t t~ h, h > b b~',
    },
    # 2HDM processes
    '2HDM': {
        'tth1_lo': 'generate p p > t t~ h1',
        'tth2_lo': 'generate p p > t t~ h2',
        'tth3_lo': 'generate p p > t t~ h3',

        'tthxbb_lo': ('generate p p > t t~ h1, h1 > b b~\n'
                      'add process p p > t t~ h2, h2 > b b~'),
    },
    # s4top_v4 processes
    "s4top_v4": {
        'tth_lo': 'generate p p > t t~ h',
        'tth2_lo': 'generate p p > t t~ h2',
        'tth3_lo': 'generate p p > t t~ h3',

        'tthtt_lo': 'generate p p > t t~ h, h > t t~',
        'tth2tt_lo': 'generate p p > t t~ h2, h2 > t t~',
        'tth3tt_lo': 'generate p p > t t~ h3, h3 > t t~',
    },
    # 2HDMtII_NLO processes
    "2HDMtII_NLO": {
        'tth1_lo': 'generate p p > t t~ h1',
        'tth2_lo': 'generate p p > t t~ h2',
        'tth3_lo': 'generate p p > t t~ h3',

        'tth1tt_lo': 'generate p p > t t~ h1, h1 > t t~',
        'tth2tt_lo': 'generate p p > t t~ h2, h2 > t t~',
        'tth3tt_lo': 'generate p p > t t~ h3, h3 > t t~',
    },
}

notes = {
    'tttt_lo': 'Four-top leading order, QCD diagrams only',
    'tttt_lo_only_qed': 'Four-top leading order, QED diagrams only',
    'tttt_lo_add_qed': 'Four-top leading order, QCD+QED diagrams',
    'tttt_nlo': 'Four-top next-to-leading order, QCD diagrams only',
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


def install_models():
    info('Installing Models')
    for i, model in enumerate(glob('models/*.zip')):
        info2('{})  {}'.format(i, model))
        # mkdir(join('MG5_amC', model[:-4]))
        sh('tar', ['-xzf', model, '-C', 'MG5_aMC/models'])


def gen_proc(cfg):
    log = open(join(RUN_NAME, cfg.job_name)+'.log', 'w')
    model_type = "model"
    if cfg.model[-3:] == "_v4":
        model_type += "_v4"
    try:
        proc = PROCS[cfg.model][cfg.proc_name]
    except KeyError:
        print("Error: Unkown process '{}' for model '{}'".format(cfg.proc_name, cfg.model))
        return
    cproc = TEMPLATE.format(proc=proc, job_name=RUN_NAME, dir_name=cfg.job_name,
                            model_type=model_type,
                            model=cfg.model,
                            beamenergy=500*cfg.comenergy, yukawa=1.73e2*cfg.yukawa)
    for pName, mass in cfg.masses:
        pdgId = pdgIds[pName]
        cproc += '\nset param_card mass {} {}'.format(pdgId, mass)
    fname = join(RUN_NAME, cfg.job_name+'.dat')
    with open(fname, 'w') as f:
        f.write(cproc)

    log.write("Running Madgraph for process \"{}\" @ {:.1f}TeV\n".format(cfg.proc_name, cfg.comenergy))
    rmtree(join(RUN_NAME, cfg.job_name), ignore_errors=True)
    sh('./MG5_aMC/bin/mg5_aMC', ['-f', fname], output=log)
    log.close()


# def read_results():
#     from bs4 import BeautifulSoup as Soup
#     class Row:
#         def __init__(self, proc, comenergy, yukawa):
#             self.proc = proc
#             self.comenergy = comenergy
#             self.yukawa = yukawa
#             self.crossx = 'N/A'
#             self.stat_err = None
#             self.scale_err = None
#             self.cs_err = None
#             self.pdf_err = None
#             self.err_str = ""
#             self.note = ""
#     scale_re = re.compile("scale variation: ({flt})% ({flt})%".format(flt=FLT_RE))
#     scale_re2 = re.compile("              {flt} pb  ({flt})% ({flt})%".format(flt=FLT_RE))
#     cs_re = re.compile("central scheme variation: ({flt})% ({flt})%".format(flt=FLT_RE))
#     pdf_re = re.compile("PDF variation: ({flt})% ({flt})%".format(flt=FLT_RE))
#     rows = []
#     for fname in glob(RUN_NAME+"/*"):
#         if not isdir(fname):
#             continue
#         _, onlyfname = split(fname)
#         proc, comenergy, yukawa = re.findall(r"([a-zA-Z_0-9]+)_([0-9\.]+)TeV_([0-9\.]+)", onlyfname)[0]
#         row = Row(proc, comenergy, yukawa)
#         try:
#             with open(join(fname, 'crossx.html')) as f:
#                 soup = Soup(f, 'html5lib')
#             text_raw = soup.select("tr")[1].select("td")[3].get_text()
#             crossx, stat_err = re.findall(r"({flt}) . ({flt})".format(flt=FLT_RE), text_raw, re.UNICODE)[0]
#             row.crossx = crossx
#             row.stat_err = stat_err
#             row.note += notes.get(proc, '')

#             # Since MG is dumb, LO systematics are stored separately from NLO systematics
#             #   ¯\_(ツ)_/¯
#             try:
#                 # get from LO place: bottom of {proc}/Events/run_01/parton_systematics.log
#                 with open(join(fname, 'Events/run_01/parton_systematics.log')) as f:
#                     txt = f.read()
#                 row.scale_err = [abs(float(s.replace(' ', ''))) for s in scale_re.findall(txt)[0]]
#                 row.cs_err = [abs(float(s.replace(' ', ''))) for s in cs_re.findall(txt)[0]]
#                 row.pdf_err = [abs(float(s.replace(' ', ''))) for s in pdf_re.findall(txt)[0]]
#             except IOError:
#                 # get from NLO place: {proc}/Events/run_01/summary.txt
#                 with open(join(fname, 'Events/run_01/summary.txt')) as f:
#                     txt = f.read()
#                 row.scale_err = [abs(float(s.replace(' ', ''))) for s in scale_re2.findall(txt)[0]]

#             row.err_str += "&#177;{:s}(stat) ".format(row.stat_err)
#             if row.scale_err is not None:
#                 row.err_str += "<font style=\"background-color:#f1f1f1\"><sup>+{:g}%</sup><sub>-{:g}%</sub>(scale)</font>".format(*row.scale_err)
#             # if row.cs_err is not None:
#             #     row.err_str += "<font style=\"background-color:#ffccff\"><sup>+{:g}%</sup><sub>-{:g}%</sub>(Central Scheme)</font>".format(*row.cs_err)
#             if row.pdf_err is not None:
#                 row.err_str += "<font style=\"background-color:#b3ffb3\"><sup>+{:g}%</sup><sub>-{:g}%</sub>(pdf)</font>".format(*row.pdf_err)

#         except IOError as e:
#             row.note += "Files missing"
#             # raise e
#         except IndexError as e:
#             row.note += "Files malformed"
#             # raise e

#         rows.append(row)

#     rows.sort(key=lambda r: r.comenergy)
#     rows.sort(key=lambda r: r.yukawa)
#     rows.sort(key=lambda r: r.proc)
#     return rows

# def gen_tables(rows):
#     info("Generating tables")
#     rows_html = [("<tr><td><a href=\"{}\">{}</a></td><td>{}</td>"
#                   "<td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>").format(dir_name(row.proc, row.comenergy, row.yukawa),
#                                                                               row.proc, row.comenergy, row.yukawa,
#                                                                               row.crossx+row.err_str, PROCS.get(row.proc, 'N/A'),
#                                                                               row.note) for row in rows]
#     header = "<tr><th>Process</th><th>COM Energy</th><th>Top Yukawa</th><th>Cross-Section (pb)</th><th>Command</th><th>Note</th></tr>"
#     table = "<table>{}<tbody>{}</tbody><table>".format(header, '\n'.join(rows_html))

#     with open(join(RUN_NAME, "summary.html"), "w") as f:
#         f.write(
# '''\
# <style>
# table {
#   border-collapse: collapse;
# }
# table, th, td {
#   border: 1px solid black;
# }
# </style>
# ''')
#         f.write(table)
#     info("Done!")

def gen_json(rows):
    info("Generating json")

    objs = []
    for row in rows:
        obj = {}
        obj['proc'] = row.proc
        obj['invocation'] = PROCS.get(row.proc, 'N/A')
        obj['comenergy'] = row.comenergy
        obj['yukawa'] = row.yukawa
        obj['crossx'] = row.crossx
        obj['stat_err'] = row.stat_err
        obj['scale_err'] = row.scale_err
        obj['cs_err'] = row.cs_err
        obj['pdf_err'] = row.pdf_err
        obj['note'] = row.note
        objs.append(obj)
    with open(join(RUN_NAME, "summary.json"), "w") as f:
        json.dump(objs, f, indent=2)
    info("Done!")

class Task(object):
    def __init__(self, **kwargs):
        if PY3:
            from string import ascii_letters as letters
        else:
            from string import letters
        from string import digits
        legal_chars = letters + digits + '_-.'

        self._setup = kwargs
        job_name = '_'.join(str(kwargs[key]) for key in sorted(list(kwargs.keys())))
        self.job_name = ''.join(l for l in job_name if l in legal_chars)
        for key, val in kwargs.items():
            setattr(self, key, val)

def main(tasks):
    if not isdir('MG5_aMC'):
        install_mg5()
        install_models()

    if tasks:
        pool = Pool(3)
        info('Generating the following processes:')
        for i, cfg in enumerate(tasks):
            info2("{:2d})  {:20s}  @ {:5.2f}TeV with ".format(i+1, cfg.proc_name, cfg.comenergy) +
                  ', '.join('{}={}'.format(key, value) for key, value in cfg._setup.items() if key not in ('proc_name', 'comenergy')))
        if not get_yes_no('Proceed?', True):
            return
        for _ in tqdm.tqdm(pool.imap_unordered(gen_proc, tasks), total=len(tasks)):
            pass

    # found_procs = read_results()
    # if args.tables:
    #     gen_tables(found_procs)

    # if args.json:
    #     gen_json(found_procs)

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
    add('-p', '--processes', nargs='+')
    add('--publish', action='store_true')
    add('--tables', action='store_true')
    add('--json', action='store_true')
    add('--nokeep', action='store_true')
    add('--noprompt', action='store_true')
    add('--comenergies', default=[13.0], type=float, nargs='+')
    add('--yukawas', default=[1.0], type=float, nargs="+")
    add('--model', default='sm')

    def mass(arg_str):
        fst, snd = arg_str.split(':')
        return fst, float(snd)
    add('--mass', action='append', default=[], type=mass, metavar='NAME:MASS')

    args = parser.parse_args()
    NO_PROMPT = args.noprompt
    RUN_NAME = args.run_name
    tasks = []
    if args.processes:
        if isdir(RUN_NAME):
            if args.nokeep or get_yes_no(RUN_NAME+' exists. Remove old results?'):
                rmtree(RUN_NAME, ignore_errors=True)
                mkdir(RUN_NAME)
        else:
            mkdir(RUN_NAME)

        # NOTE: Update logic here to add additional configuration
        for comenergy, yukawa in product(args.comenergies, args.yukawas):
            tasks.extend(Task(model=args.model,
                              proc_name=proc_name,
                              comenergy=comenergy,
                              yukawa=yukawa,
                              masses=args.mass)
                         for proc_name in args.processes)

        all_tasks = {task.job_name: task for task in tasks}
        dill_filename = join(RUN_NAME, 'batch.dill')
        if not args.nokeep and isfile(dill_filename):
            with open(dill_filename, 'rb') as f:
                all_tasks.update(dill.load(f))

        with open(dill_filename, 'wb') as f:
            dill.dump(all_tasks, f)

    main(tasks)
