from os.path import join, isfile, split
import argparse
import time

from metis.CMSSWTask import CMSSWTask
from metis.Sample import DirectorySample
from metis.StatsParser import StatsParser

from utils import read_param, pdgIds

TASKS = {}

def read_tasks():
    global TASKS
    from dill import load
    with open(join(RUN_NAME, 'batch.dill'), 'r') as f:
        TASKS = load(f)

def unzip_lhe(task):
    from gzip import open as zopen
    lhe_fname = join(RUN_NAME,task.job_name, 'Events', 'run_01', 'unweighted_events.lhe')
    lhegz_fname = lhe_fname + '.gz'
    if not isfile(lhe_fname):
        if not isfile(lhegz_fname):
            raise ValueError('no lhe or gzipped file exists')
        with zopen(lhegz_fname) as f:
            lhe = f.read()
        with open(lhe_fname, 'w') as f:
            f.write(lhe)
    return lhe_fname

# ktstrs = [str(round(kt,1)).replace(".","p") for kt in np.arange(0.4,2.2,0.1)]
# # ktstrs = [str(round(kt,1)).replace(".","p") for kt in np.arange(0.4,0.5,0.1)]
# runstrs = ["{:02d}".format(i) for i in range(1,len(ktstrs)+1)]

def submit():
    total_summary = {}
    for job_name, task in TASKS.items():
        # for runstr,ktstr in zip(runstrs,ktstrs):
        try:
            lhe_fname = unzip_lhe(task)
        except ValueError:
            continue
        lhe_dir = split(lhe_fname)[0]
        zp_mass = read_param(RUN_NAME, task, 'MASS', pdgIds['zp'])
        gt = read_param(RUN_NAME, task, 'ZPRIME', 1)

        if zp_mass != 100.0 or gt not in (0.0, 1.0): continue
        lhe = CMSSWTask(
                sample = DirectorySample(
                    location=lhe_dir,
                    globber="*.lhe",
                    dataset="/tttt-ZPrime/M_Zp{}-g_tZp{}/LHE".format(zp_mass, gt),
                    ),
                events_per_output = 100,
                total_nevents = 10000,
                # pset = "pset_gensim.py",
                pset = "lhe_proc/step0_cfg.py",
                cmssw_version = "CMSSW_9_4_6_patch1",
                split_within_files = True,
                )

        raw = CMSSWTask(
                sample = DirectorySample(
                    location = lhe.get_outputdir(),
                    dataset = lhe.get_sample().get_datasetname().replace("LHE","RAW"),
                    ),
                open_dataset = True,
                files_per_output = 1,
                # pset = "pset_raw.py",
                pset = "lhe_proc/step1_cfg.py",
                cmssw_version = "CMSSW_9_4_6_patch1",
                )

        aod = CMSSWTask(
                sample = DirectorySample(
                    location = raw.get_outputdir(),
                    dataset = raw.get_sample().get_datasetname().replace("RAW","AOD"),
                    ),
                open_dataset = True,
                files_per_output = 5,
                # pset = "pset_aod.py",
                pset = "lhe_proc/step2_cfg.py",
                cmssw_version = "CMSSW_9_4_6_patch1",
                )

        miniaod = CMSSWTask(
                sample = DirectorySample(
                    location = aod.get_outputdir(),
                    dataset = aod.get_sample().get_datasetname().replace("AOD","MINIAOD"),
                    ),
                open_dataset = True,
                flush = True,
                files_per_output = 10,
                # pset = "pset_miniaod.py",
                pset = "lhe_proc/step3_cfg.py",
                cmssw_version = "CMSSW_9_4_6_patch1",
                )

        tasks = [lhe,raw,aod,miniaod]

        for task in tasks:
            task.process()
            summary = task.get_task_summary()
            total_summary[task.get_sample().get_datasetname()] = summary

    StatsParser(data=total_summary, webdir="~/public_html/dump/zp_studies/").do()
    # time.sleep(2.0*3600)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run MG for TTTT Studies')
    add = parser.add_argument
    add('run_name')

    args = parser.parse_args()
    RUN_NAME = args.run_name

    read_tasks()
    submit()
