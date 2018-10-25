#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from __future__ import print_function
import argparse
import sys
from os.path import join
from collections import defaultdict

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotboard as mpb
from matplottery.utils import Hist1D, to_html_table
from utils import read_cross_section, read_param

import numpy as np

TASKS = {}
HISTS = {}

RUN_NAME = "procs"

def get_label(task):
    h1_mass = read_param(RUN_NAME, task, 'MASS', 25)
    h2_mass = read_param(RUN_NAME, task, 'MASS', 35)
    return "$M_h={:.1f}, M_H={:.1f}$".format(h1_mass, h2_mass)

def hist_plot(h, include_errors=False, line_width=1, **kwargs):

    counts = h.counts
    edges = h.edges
    left, right = edges[:-1], edges[1:]
    x = np.array([left, right]).T.flatten()
    y = np.array([counts, counts]).T.flatten()

    plt.plot(x, y, linewidth=line_width, **kwargs)
    if include_errors:
        if h.errors_up is not None:
            errors = np.vstack((h.errors_down, h.errors_up))
        else:
            errors = h.errors
        plt.errorbar(h.bin_centers, h.counts, yerr=errors,
                     color='k', marker=None, linestyle='None',
                     barsabove=True, elinewidth=.7, capsize=1)


def read_tasks():
    global TASKS
    from dill import load
    with open(join(RUN_NAME, 'batch.dill'), 'r') as f:
        TASKS = load(f)

def fill_hists():
    import gzip
    from pylhe import readLHE

    pt_bins = np.linspace(0, 1500, 10, endpoint=True)
    eta_bins = np.linspace(-7, 7, 10, endpoint=True)
    phi_bins = np.linspace(-3.14159, 3.14159, 10, endpoint=True)

    for task in TASKS.values():
        filename = join(RUN_NAME, task.job_name, 'Events', 'run_01', 'unweighted_events.lhe.gz')
        top_pt = []
        top_eta = []
        top_phi = []
        higgs_pt = []
        higgs_eta = []
        higgs_phi = []
        with gzip.open(filename, 'r') as f:
            events = readLHE(f)
            for i, event in enumerate(events):
                for p in event.particles:
                    if abs(p.id) == 6:
                        top_pt.append(p.pt)
                        top_eta.append(p.eta)
                        top_phi.append(p.phi)
                    elif abs(p.id) in (25, 35):
                        higgs_pt.append(p.pt)
                        higgs_eta.append(p.eta)
                        higgs_phi.append(p.phi)
                # if i > 1000: break
        HISTS[(task.job_name, 'top_pt')] = Hist1D(top_pt, bins=pt_bins)
        HISTS[(task.job_name, 'top_eta')] = Hist1D(top_eta, bins=eta_bins)
        HISTS[(task.job_name, 'top_phi')] = Hist1D(top_phi, bins=phi_bins)

        HISTS[(task.job_name, 'higgs_pt')] = Hist1D(higgs_pt, bins=pt_bins)
        HISTS[(task.job_name, 'higgs_eta')] = Hist1D(higgs_eta, bins=eta_bins)
        HISTS[(task.job_name, 'higgs_phi')] = Hist1D(higgs_phi, bins=phi_bins)

@mpb.decl_fig
def multiplot(tasks, plot_name, proc_name=None):

    rows = []
    row_labels = []
    for task in tasks.values():
        if proc_name and task.proc_name != proc_name:
            continue
        label = get_label(task)
        hist_plot(HISTS[(task.job_name, plot_name)], label=label)
        cross_section, error = read_cross_section(RUN_NAME, task)
        rows.append([read_param(RUN_NAME, task, 'MASS', 25),
                     read_param(RUN_NAME, task, 'MASS', 35),
                     '{}+-{}'.format(cross_section, error)])
        row_labels.append(task.proc_name)
    plt.legend()
    plt.ylim((0,None))
    return to_html_table(rows, ['', '$m_h$ (GeV)', '$m_H$ (GeV)', r'$\sigma$ (pb)'], row_labels, 'table-condensed')


def make_plots(build=False, publish=False):

    figures = {}
    for proc_name in ['tth1_lo', 'tth2_lo']:
        figures['top_pt_'+proc_name] = multiplot(TASKS, 'top_pt', proc_name)
        figures['top_eta_'+proc_name] = multiplot(TASKS, 'top_eta', proc_name)
        figures['top_phi_'+proc_name] = multiplot(TASKS, 'top_phi', proc_name)

        figures['higgs_pt_'+proc_name] = multiplot(TASKS, 'higgs_pt', proc_name)
        figures['higgs_eta_'+proc_name] = multiplot(TASKS, 'higgs_eta', proc_name)
        figures['higgs_phi_'+proc_name] = multiplot(TASKS, 'higgs_phi', proc_name)

    mpb.render(figures, build=build)
    mpb.generate_report(figures, '2HDM Studies',
                        output='hists.html',
                        source=__file__)

    if publish:
        mpb.publish()


def report():

    const_h1s = []
    const_h2s = []
    for task in TASKS.values():
        xs = read_cross_section(RUN_NAME, task)
        if task.proc_name == 'tth1_lo' and read_param(RUN_NAME, task, 'MASS', 25) == 125:
            m = read_param(RUN_NAME, task, 'MASS', 35)
            const_h1s.append((m, xs))
        if task.proc_name == 'tth2_lo' and read_param(RUN_NAME, task, 'MASS', 35) == 125:
            m = read_param(RUN_NAME, task, 'MASS', 25)
            const_h2s.append((m, xs))

    const_h1s.sort()
    const_h2s.sort()

    for m, xs in const_h1s:
        print(m, xs[0])
    print()
    for m, xs in const_h2s:
        print(m, xs[0])

    print('SM')
    for task in TASKS.values():
        if task.proc_name == 'tth_lo':
            print(read_cross_section(RUN_NAME, task))
            break

    print('h1 + h2')
    h1h2 = 0
    h = 0
    for task in TASKS.values():
        if task.proc_name == 'tthxbb_lo':
            h1h2 = read_cross_section(RUN_NAME, task)
        elif task.proc_name == 'tthbb_lo':
            h = read_cross_section(RUN_NAME, task)
    print('h1+h2', h1h2)
    print('sm h', h)

    print('ratios')
    pairs = defaultdict(dict)
    for task in TASKS.values():
        xs = read_cross_section(RUN_NAME, task)
        try:
            m1 = read_param(RUN_NAME, task, 'MASS', 25)
            m2 = read_param(RUN_NAME, task, 'MASS', 35)
        except:
            continue
        if m1 != m2:
            continue
        if task.proc_name == 'tth1_lo':
            pairs[m1]['h1'] = xs
        elif task.proc_name == 'tth2_lo':
            pairs[m1]['h2'] = xs
    for mass, xss in pairs.items():
        if len(xss) == 2:
            h1 = xss['h1'][0]
            h2 = xss['h2'][0]
            print('{:10.4f} {:10.4f} {:10.4f} {:10.4f}'.format(mass, h1, h2, h1/h2))



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run MG for TTTT Studies')
    add = parser.add_argument
    add('run_name')
    add('--publish', action='store_true')
    add('--build', action='store_true')
    add('--listtasks', action='store_true')
    add('--report', action='store_true')

    args = parser.parse_args()

    from os.path import expanduser
    mpb.configure(output_dir='ft_gen_kinematics',
                  multiprocess=False,
                  publish_remote="local",
                  publish_dir=expanduser("~/public_html/FT/"),
                  publish_url="t3.unl.edu/~cfangmeier/FT/",
                  early_abort=True,
                  )

    RUN_NAME = args.run_name
    read_tasks()
    if args.report:
        report()
    if args.listtasks:
        for i, task in enumerate(TASKS.values()):
            print('{}) '.format(i), task.job_name)
    if args.build:
        fill_hists()
    make_plots(build=args.build, publish=args.publish)
