#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from __future__ import print_function
import argparse
from os.path import join
from json import load
from itertools import groupby
import matplotlib 
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from ft_tools.results import Run

def get_theory_numbers():

    def xs(yt):
        return 9.997 + (-1.547)*yt**2 + 1.168*yt**4

    yts = [n*0.1 for n in range(21)]
    xss = [xs(yt) for yt in yts]
    return yts, xss


def plot_xsection_v_yukawa(job_name):
    with open(join(job_name, 'summary.json'), 'r') as f:
        data = load(f)
    data.sort(key=lambda x: x['proc'])
    data = {proc_id: list(procs)
            for proc_id, procs in groupby(data, lambda x: x['proc'])}
    for proc_id, procs in data.items():
        xs = []
        ys = []
        for proc in procs:
            xs.append(float(proc['yukawa']))
            ys.append(float(proc['crossx'])*1000)
        data[proc_id] = (xs, ys)
    th_xs, th_ys = get_theory_numbers()

    plt.figure()
    plt.subplot(121)

    for proc_id, (xs, ys) in data.items():
        plt.plot(xs, ys, label=proc_id)
    plt.plot(th_xs, th_ys, label='theory paper')
    plt.legend(loc='best')
    plt.semilogy()
    plt.ylabel('cross-section (fb)')
    plt.xlabel('$y_t$')

    plt.subplot(122)
    full = data['tttt_lo_add_qed']
    plt.plot(full[0], full[1], label='tttt_lo_add_qed')
    plt.plot(th_xs, th_ys, label='theory paper')
    plt.legend(loc='best')
    plt.ylabel('cross-section (fb)')
    plt.xlabel('$y_t$')


    plt.savefig('xsection_v_yukawa.png')



def main(args):
    plot_xsection_v_yukawa(args.job_name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Make Plots for TTTT MG Studies")
    add = parser.add_argument
    add('job_name')

    args = parser.parse_args()
    main(args)
