#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from __future__ import print_function
import argparse
from glob import glob
from os import rename, walk, chmod
from os.path import isfile, isdir, expanduser, join, split
from subprocess import call, STDOUT
from multiprocessing import Pool
from itertools import product
import json
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

FLT_RE = r"(?:|\+ ?|- ?)\d+\.?\d*(?:[eE][+-]\d+)?"

JOB_NAME = "procs"

TEMPLATE = '''
define p = p b b~
define j = p
{proc}
output {job_name}/{dir_name}/
launch
set run_card ebeam1 {beamenergy}
set run_card ebeam2 {beamenergy}
set param_card yukawa 6 {yukawa}
'''
# set run_card etab 5
# set run_card etal 5

PROCS = {
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


def dir_name(proc_name, comenergy, yukawa):
    if type(comenergy) is str:
        comenergy = float(comenergy)
    return '{proc_name}_{comenergy:.1f}TeV_{yukawa}'.format(proc_name=proc_name, comenergy=comenergy, yukawa=yukawa)


def gen_proc(cfg):
    # job_name, proc_name, comenergy, yukawa = args
    dir_name_ = dir_name(cfg.proc_name, cfg.comenergy, cfg.yukawa)
    log = open(join(JOB_NAME, dir_name_)+'.log', 'w')
    cproc = TEMPLATE.format(proc=PROCS[cfg.proc_name], job_name=JOB_NAME, dir_name=dir_name_,
                            beamenergy=500*cfg.comenergy, yukawa=1.73e2*cfg.yukawa)
    fname = join(JOB_NAME, dir_name_+'.dat')
    with open(fname, 'w') as f:
        f.write(cproc)

    log.write("Running Madgraph for process \"{}\" @ {:.1f}TeV".format(cfg.proc_name, cfg.comenergy))
    sh('rm', ['-rf', join(JOB_NAME, dir_name_)], output=log)
    sh('./MG5_aMC/bin/mg5_aMC', ['-f', fname], output=log)
    log.close()


def read_results():
    from bs4 import BeautifulSoup as Soup
    class Row:
        def __init__(self, proc, comenergy, yukawa):
            self.proc = proc
            self.comenergy = comenergy
            self.yukawa = yukawa
            self.crossx = 'N/A'
            self.stat_err = None
            self.scale_err = None
            self.cs_err = None
            self.pdf_err = None
            self.err_str = ""
            self.note = ""
    scale_re = re.compile("scale variation: ({flt})% ({flt})%".format(flt=FLT_RE))
    scale_re2 = re.compile("              {flt} pb  ({flt})% ({flt})%".format(flt=FLT_RE))
    cs_re = re.compile("central scheme variation: ({flt})% ({flt})%".format(flt=FLT_RE))
    pdf_re = re.compile("PDF variation: ({flt})% ({flt})%".format(flt=FLT_RE))
    rows = []
    for fname in glob(JOB_NAME+"/*"):
        if not isdir(fname):
            continue
        _, onlyfname = split(fname)
        proc, comenergy, yukawa = re.findall(r"([a-zA-Z_0-9]+)_([0-9\.]+)TeV_([0-9\.]+)", onlyfname)[0]
        row = Row(proc, comenergy, yukawa)
        try:
            with open(join(fname, 'crossx.html')) as f:
                soup = Soup(f, 'html5lib')
            text_raw = soup.select("tr")[1].select("td")[3].get_text()
            crossx, stat_err = re.findall(r"({flt}) . ({flt})".format(flt=FLT_RE), text_raw, re.UNICODE)[0]
            row.crossx = crossx
            row.stat_err = stat_err
            row.note += notes.get(proc, '')

            # Since MG is dumb, LO systematics are stored separately from NLO systematics
            #   ¯\_(ツ)_/¯
            try:
                # get from LO place: bottom of {proc}/Events/run_01/parton_systematics.log
                with open(join(fname, 'Events/run_01/parton_systematics.log')) as f:
                    txt = f.read()
                row.scale_err = [abs(float(s.replace(' ', ''))) for s in scale_re.findall(txt)[0]]
                row.cs_err = [abs(float(s.replace(' ', ''))) for s in cs_re.findall(txt)[0]]
                row.pdf_err = [abs(float(s.replace(' ', ''))) for s in pdf_re.findall(txt)[0]]
            except IOError:
                # get from NLO place: {proc}/Events/run_01/summary.txt
                with open(join(fname, 'Events/run_01/summary.txt')) as f:
                    txt = f.read()
                row.scale_err = [abs(float(s.replace(' ', ''))) for s in scale_re2.findall(txt)[0]]

            row.err_str += "&#177;{:s}(stat) ".format(row.stat_err)
            if row.scale_err is not None:
                row.err_str += "<font style=\"background-color:#f1f1f1\"><sup>+{:g}%</sup><sub>-{:g}%</sub>(scale)</font>".format(*row.scale_err)
            # if row.cs_err is not None:
            #     row.err_str += "<font style=\"background-color:#ffccff\"><sup>+{:g}%</sup><sub>-{:g}%</sub>(Central Scheme)</font>".format(*row.cs_err)
            if row.pdf_err is not None:
                row.err_str += "<font style=\"background-color:#b3ffb3\"><sup>+{:g}%</sup><sub>-{:g}%</sub>(pdf)</font>".format(*row.pdf_err)

        except IOError as e:
            row.note += "Files missing"
            # raise e
        except IndexError as e:
            row.note += "Files malformed"
            # raise e

        rows.append(row)

    rows.sort(key=lambda r: r.comenergy)
    rows.sort(key=lambda r: r.yukawa)
    rows.sort(key=lambda r: r.proc)
    return rows

def gen_tables(rows):
    info("Generating tables")
    rows_html = [("<tr><td><a href=\"{}\">{}</a></td><td>{}</td>"
                  "<td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>").format(dir_name(row.proc, row.comenergy, row.yukawa),
                                                                              row.proc, row.comenergy, row.yukawa,
                                                                              row.crossx+row.err_str, PROCS.get(row.proc, 'N/A'),
                                                                              row.note) for row in rows]
    header = "<tr><th>Process</th><th>COM Energy</th><th>Top Yukawa</th><th>Cross-Section (pb)</th><th>Command</th><th>Note</th></tr>"
    table = "<table>{}<tbody>{}</tbody><table>".format(header, '\n'.join(rows_html))

    with open(join(JOB_NAME, "summary.html"), "w") as f:
        f.write(
'''\
<style>
table {
  border-collapse: collapse;
}
table, th, td {
  border: 1px solid black;
}
</style>
''')
        f.write(table)
    info("Done!")

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
    with open(join(JOB_NAME, "summary.json"), "w") as f:
        json.dump(objs, f, indent=2)
    info("Done!")

class RunConfig:
    def __init__(self, proc_name, comenergy, yukawa):
        self.proc_name = proc_name
        self.comenergy = comenergy
        self.yukawa = yukawa


def main(args):
    if not isdir('MG5_aMC'):
        install_mg5()
    tasks = []
    if args.all:
        for comenergy, yukawa in product(args.comenergies, args.yukawas):
            tasks.extend(RunConfig(proc_name, comenergy, yukawa) for proc_name in PROCS
                             if not isdir(dir_name(proc_name, comenergy, yukawa)))
    elif args.processes:
        for comenergy, yukawa in product(args.comenergies, args.yukawas):
            tasks.extend(RunConfig(proc_name, comenergy, yukawa) for proc_name in args.processes
                             if not isdir(dir_name(proc_name, comenergy, yukawa)))
    if tasks:
        pool = Pool(3)
        info('Generating the following processes:')
        for i, cfg in enumerate(tasks):
            info2("{:2d})  {:20s}  @ {:5.2f}TeV with yt={}".format(i+1, cfg.proc_name, cfg.comenergy, cfg.yukawa))
        info('Proceed? (Y/n)')
        if raw_input().strip().lower() not in ('', 'y'):
            return
        sh('mkdir', ['-p', JOB_NAME])
        for _ in tqdm.tqdm(pool.imap_unordered(gen_proc, tasks), total=len(tasks)):
            pass

    found_procs = read_results()
    if args.tables:
        gen_tables(found_procs)

    if args.json:
        gen_json(found_procs)

    # if args.scalecard is not None:
    #     scale_card()

    if args.publish:
        pubdir = join(expanduser('~'), 'public_html')
        info('Copying output to ' + pubdir)
        procdir = join(pubdir, args.job_name)

        sh('rm', ['-rf', procdir])
        sh('cp', ['-r', args.job_name, pubdir])

        info('Fixing permissions...')

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
    add('job_name')
    add('-p', '--processes', nargs='+')
    add('--all', action='store_true')
    add('--publish', action='store_true')
    add('--tables', action='store_true')
    add('--json', action='store_true')
    # add('--scalecard', type=float, nargs=2)  # lumi and then energy
    add('--comenergies', default=[13.0], type=float, nargs='+')
    add('--yukawas', default=[1.0], type=float, nargs="+")

    args = parser.parse_args()
    JOB_NAME = args.job_name
    main(args)
