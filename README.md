FTGenStudies
============

# How to Run

First, clone the repository and execute the setup script to install madgraph and customize a few settings

``` bash
./setup.sh
```

Second, run the following command to generate all of the processes

``` bash
./setup.sh make_procs
```

The first time this may take a few minutes as MG needs to download and compile some extra tools.
Finally, you can generate events/calculate x-sections with:

``` bash
./setup.sh gen_events
```
