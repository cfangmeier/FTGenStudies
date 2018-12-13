#!/bin/bash

## CONFIGURATION

CMSVER="CMSSW_9_4_6_patch1"
CONDITIONS="94X_mc2017_realistic_v14"
LHE_IN="unweighted_events.lhe"
if [ $# -ge 1 ]; then
  LHE_IN=$1
fi
n=10000
THREADS=4

## SETUP (and build if necessary)

source /cvmfs/cms.cern.ch/cmsset_default.sh
export SCRAM_ARCH=slc6_amd64_gcc630
if [ -r ${CMSVER}/src ] ; then 
 echo release ${CMSVER} already exists
else
scram p CMSSW ${CMSVER}
fi
cd ${CMSVER}/src
eval `scram runtime -sh`

scram b
cd ../../

###########################################################
## Step 0 (LHE -> GEN-SIM)
###########################################################
if [ ! -f step0_cfg.py ]; then
  mkdir -p ${CMSVER}/src/Configuration/GenProduction/python/
  cp step0-fragment.py ${CMSVER}/src/Configuration/GenProduction/python/step0-fragment.py
  cmsDriver.py Configuration/GenProduction/python/step0-fragment.py \
      --filein file:${LHE_IN} \
      --fileout file:step0.root \
      --mc \
      --eventcontent RAWSIM \
      --datatier GEN-SIM \
      --conditions ${CONDITIONS} \
      --beamspot Realistic25ns13TeVEarly2017Collision \
      --step GEN,SIM \
      --nThreads ${THREADS} \
      --geometry DB:Extended \
      --era Run2_2017 \
      --python_filename step0_cfg.py \
      --no_exec \
      --customise Configuration/DataProcessing/Utils.addMonitoring \
      -n ${n} || exit $? ;
fi

###########################################################
## Step 1 (GEN-SIM -> GEN-SIM-RAW)
###########################################################
if [ ! -f step1_cfg.py ]; then
cmsDriver.py step1 \
    --filein file:step0.root \
    --fileout file:step1.root \
    --pileup_input "dbs:/Neutrino_E-10_gun/RunIISummer17PrePremix-MCv2_correctPU_94X_mc2017_realistic_v9-v1/GEN-SIM-DIGI-RAW" \
    --mc \
    --eventcontent PREMIXRAW \
    --datatier GEN-SIM-RAW \
    --conditions ${CONDITIONS} \
    --step DIGIPREMIX_S2,DATAMIX,L1,DIGI2RAW,HLT:2e34v40 \
    --nThreads ${THREADS} \
    --datamix PreMix \
    --era Run2_2017 \
    --python_filename step1_cfg.py \
    --no_exec \
    --customise Configuration/DataProcessing/Utils.addMonitoring \
    -n ${n} || exit $? ;
fi

###########################################################
## Step 2 (GEN-SIM-RAW -> AOD-SIM)
###########################################################

if [ ! -f step2_cfg.py ]; then
cmsDriver.py step2 \
    --filein file:step1.root \
    --fileout file:step2.root \
    --mc \
    --eventcontent AODSIM \
    --runUnscheduled \
    --datatier AODSIM \
    --conditions ${CONDITIONS} \
    --step RAW2DIGI,RECO,RECOSIM,EI \
    --nThreads ${THREADS} \
    --era Run2_2017 \
    --python_filename step2_cfg.py \
    --no_exec \
    --customise Configuration/DataProcessing/Utils.addMonitoring \
    -n ${n} || exit $? ; 
fi

###########################################################
## Step 3 (AOD-SIM -> MINIAODSIM)
###########################################################

if [ ! -f step3_cfg.py ]; then
  cmsDriver.py step3 \
      --filein file:step2.root \
      --fileout file:step3.root \
      --mc \
      --eventcontent MINIAODSIM \
      --runUnscheduled \
      --datatier MINIAODSIM \
      --conditions ${CONDITIONS} \
      --step PAT \
      --nThreads ${THREADS} \
      --scenario pp \
      --era Run2_2017,run2_miniAOD_94XFall17 \
      --python_filename step3_cfg.py \
      --no_exec \
      --customise Configuration/DataProcessing/Utils.addMonitoring \
      -n ${n} || exit $? ;
fi

# After this point, abort if anything goes wrong
set -e

if [ -f ${LHE_IN} -a ! -f step0.root ]; then
  cmsRun step0_cfg.py
fi

if [ -f step0.root -a ! -f step1.root ]; then
  cmsRun step1_cfg.py
fi

if [ -f step1.root -a ! -f step2.root ]; then
  cmsRun step2_cfg.py
fi

if [ -f step2.root -a ! -f step3.root ]; then
  cmsRun step3_cfg.py
fi
