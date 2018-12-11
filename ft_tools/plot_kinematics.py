#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from __future__ import print_function
import argparse
import sys
from os.path import join, isfile, realpath
from collections import defaultdict
from itertools import product
import logging

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

import matplotboard as mpb
from matplottery.utils import Hist1D, to_html_table
from lhe2sqlite import convert

from utils import read_cross_section, read_param, pdgIds

TASKS = {}
HISTS = {}

RUN_NAME = "procs"

PT_BINS = np.linspace(0, 1500, 20, endpoint=True)
ETA_BINS = np.linspace(-7, 7, 20, endpoint=True)


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
    for task in TASKS.values():
        print('loading task', task.job_name)
        filename = join(RUN_NAME, task.job_name, 'Events', 'run_01', 'unweighted_events.lhe.gz')
        sql_filename = realpath(filename[:-7]+'.sqlite3')
        if not isfile(sql_filename):
            print('converting', filename, '->', sql_filename)
            try:
                convert(filename, sql_filename)
            except Exception as e:
                print(e)
                continue

        df = pd.read_sql_query(('select px, py, pz from particle '
                                'where abs(pdgid)==6 and abs(status)==1'),
                               'sqlite:///'+sql_filename)
        df['pt'] = np.sqrt(df['px']**2 + df['py']**2)
        df['p'] = np.sqrt(df['px']**2 + df['py']**2 + df['pz']**2)
        df['eta'] = np.arctanh(df['pz'] / df['p'])

        HISTS[(task, 'top_pt')] = Hist1D(np.array(df['pt']), bins=PT_BINS)
        HISTS[(task, 'top_eta')] = Hist1D(np.array(df['eta']), bins=ETA_BINS)

        for k, h in HISTS.items():
            HISTS[k] = h / h.integral


@mpb.decl_fig
def multiplot(tasks, plot_name):

    # rows = []
    # row_labels = []
    labels = {
        'tth1tt_lo': 'p p > t t~ h1, h1 > t t~',
        'tth2tt_lo': 'p p > t t~ h2, h2 > t t~',
        'tth3tt_lo': 'p p > t t~ h3, h3 > t t~',
    }
    for task in tasks.values():
        if proc_name and task.proc_name != proc_name:
            continue
        # label = get_label(task)
        label = str(id(task))
        hist_plot(HISTS[(task.job_name, plot_name)], label=label)
        cross_section, error = read_cross_section(RUN_NAME, task)
        # rows.append([read_param(RUN_NAME, task, 'MASS', 25),
        #              read_param(RUN_NAME, task, 'MASS', 35),
        #              '{}+-{}'.format(cross_section, error)])
        # row_labels.append(task.proc_name)
    plt.legend()
    plt.ylim((0,None))
    # return to_html_table(rows, ['', '$m_h$ (GeV)', '$m_H$ (GeV)', r'$\sigma$ (pb)'], row_labels, 'table-condensed')


@mpb.decl_fig
def zp_xs_v_gt(proc_name):
    from labellines import labelLines
    mass_sets = defaultdict(list)
    sm_val = 0
    for task in TASKS.values():
        if task.proc_name != proc_name: continue
        try:
            zp_mass = read_param(RUN_NAME, task, 'MASS', pdgIds['zp'])
            gt = read_param(RUN_NAME, task, 'ZPRIME', 1)
            xs = read_cross_section(RUN_NAME, task)
            mass_sets[zp_mass].append((gt, xs[0]))
            if gt == 0:
                sm_val = xs[0]
        except:
            continue
    masses = sorted(mass_sets.keys())
    for zp_mass in masses:
        points = mass_sets[zp_mass]
        points.sort()
        xs, ys = zip(*points)
        ys = [y/sm_val for y in ys]
        plt.plot(xs, ys, '--g', label=str(zp_mass))
    plt.ylim((0.95, 8))
    plt.xlim((0, 2))
    plt.xlabel('$g_{tZ\'}$', fontsize='xx-large')
    plt.ylabel(r'$\sigma_{NP+SM} / \sigma_{SM}(pp \rightarrow t\bar{t}t\bar{t})$', fontsize='xx-large')
    plt.yticks([1, 2, 3, 4, 5, 6, 7, 8])
    plt.xticks([0, 0.5, 1.0, 1.5, 2.0])
    plt.minorticks_on()
    plt.grid(which='minor', alpha=0.5)
    plt.grid(which='major')
    # plt.legend()
    labelLines(plt.gca().get_lines(),
               zorder=2.5,
               backgroundcolor='white',
               xvals=(0.12, 1.15),
               )


@mpb.decl_fig
def zp_kinem_v_m(gt=0.1, var='pt', proc_name='tttt_lo'):
    for idx, mass in enumerate([25, 50, 75, 100, 125]):
        for task in TASKS.values():
            try:
                zp_mass = read_param(RUN_NAME, task, 'MASS', pdgIds['zp'])
                task_gt = read_param(RUN_NAME, task, 'ZPRIME', 1)
                # print(proc_name, task.proc_name)
                if zp_mass == mass and task_gt == gt and task.proc_name == proc_name:
                    dist = HISTS[(task, 'top_'+var)]
                    hist_plot(dist,
                              label='$M_{Z\'}$='+str(mass)+'GeV',
                              include_errors=True, alpha=0.75)
                    break
            except Exception as e:
                logging.exception(e)
                continue
    plt.legend(loc='upper right')
    if var == 'pt':
        plt.ylim((0, 0.4))
        plt.xlabel(r'$p_T$', fontsize='xx-large')
    else:  # eta
        plt.ylim((0, 0.25))
        plt.xlabel(r'$\eta$', fontsize='xx-large')
    plt.text(0.1, 0.3, '$g_t={}$'.format(gt), transform=plt.gca().transAxes)


def make_plots(build=False, publish=False):

    figures = {}

    for proc_name in ['tttt_lo', 'tttt_fixedorder_lo']:
        pfx = 'zp_{}_'.format(proc_name)
        figures[pfx+'xs_v_gt'] = zp_xs_v_gt(proc_name)
        for var, gt in product(['pt', 'eta'],
                               [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]):
            gt_s = '{:.1f}'.format(gt).replace('.', 'p')
            figures[pfx+'top_{}_v_m_{}'.format(var, gt_s)] = zp_kinem_v_m(gt, var, proc_name)


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
    mpb.configure(output_dir='z_prime_studies',
                  multiprocess=False,
                  publish_remote="local",
                  publish_dir=expanduser("~/public_html/FT/"),
                  publish_url="t3.unl.edu/~cfangmeier/FT/",
                  early_abort=True,
                  )
    # mpb.configure(output_dir='z_prime_studies/',
    #               multiprocess=False,
    #               publish_remote="cfangmeier@t3.unl.edu",
    #               publish_dir="~/public_html/FT/",
    #               publish_url="t3.unl.edu/~cfangmeier/FT/",
    #               early_abort=True,
    #               )

    RUN_NAME = args.run_name
    read_tasks()
    if args.report:
        report()
    if args.listtasks:
        for i, task in enumerate(TASKS.values()):
            print('{}) '.format(i), task.proc_name)
    if args.build:
        # fill_hists(100)
        fill_hists()
    make_plots(build=args.build, publish=args.publish)
