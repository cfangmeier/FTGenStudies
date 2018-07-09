set -e

if [ ! -d MG5_aMC ]; then
    wget http://launchpad.net/madgraph5/2.0/2.6.x/+download/MG5_aMC_v2.6.3.2.tar.gz
    tar -xf MG5_aMC_v2.6.3.2.tar.gz
    rm MG5_aMC_v2.6.3.2.tar.gz
    mv MG5_aMC_v2_6_3_2 MG5_aMC
    sed -e "s/# automatic_html_opening = .*/automatic_html_opening = False/" -i MG5_aMC/input/mg5_configuration.txt
fi

if [ "$1" = "make_procs" ]; then
    echo "  Generating configuration for all processes. Note that if this is the first time running with make_procs, it may take some time as the NLO"
    echo "  samples will require extra tools that need to be downloaded and compiled. This may be a good time to get a coffee. :)"
    rm -rf procs/
    mkdir procs/
    for filename in *.dat; do
        echo "Building process in $filename"
        cp $filename ${filename}.tmp
        echo "output procs/${filename%.*} -nojpeg" >> ${filename}.tmp
        ./MG5_aMC/bin/mg5_aMC -f ${filename}.tmp
        rm ${filename}.tmp
    done
fi

if [ "$1" = "gen_events" ]; then
    for filename in *.dat; do
        proc="${filename%.*}"
        echo "generating events for $proc"
        ./procs/${proc}/bin/generate_events -f
    done
fi
