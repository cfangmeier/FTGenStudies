#!/usr/bin/env zsh

release="CMSSW_9_2_8"

if [ ! -d "$release" ]; then
    cmsrel $release
fi

cd ${release}/src/
cmsenv
cd -

echo "Environment setup!"
echo "run \"pip install -r requirements.txt --user\" to install python dependencies"
