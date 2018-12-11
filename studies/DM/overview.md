# DM Studies


## Some Links
  1. [CADI](http://cms.cern.ch/iCMS/analysisadmin/cadilines?id=1824&ancode=EXO-16-049&tp=an&line=EXO-16-049)
  2. [AN](http://cms.cern.ch/iCMS/jsp/db_notes/noteInfo.jsp?cmsnoteid=CMS%20AN-2016/417)
  3. [DIS](http://uaf-8.t2.ucsd.edu/~namin/dis/) search for /TTbarDMJets*/*/*
  4. [Generator fragment example](https://cms-pdmv.cern.ch/mcm/public/restapi/requests/get_fragment/EXO-RunIISummer15wmLHEGS-01586)
  5. [MC cards example](https://github.com/cms-sw/genproductions/tree/02c6e5b080dc6e6a5d9ab8fb16b793505262e14d/bin/MadGraph5_aMCatNLO/cards/production/13TeV/DarkMatter/DMPseudo_ttbar_dilep/DMPseudoscalar_ttbar01j_mphi_100_mchi_10_gSM_1p0_gDM_1p0)


## Notes
  - In the AN, reference 18 points to [here][https://svnweb.cern.ch/cern/wsvn/LHCDMF/trunk/models/HF_S%2BPS/contributed_by_KristianHahn/?#abad0c22e163585557a6e88956511f7f3] which is an SVN share containing madgraph model files for both scalar and pseudoscalar DM mediator models. I downloaded them and placed them in `models/`. The models are called:
    - `DMScalar`
    - `DMPseudo`
  - Now, the task is to attempt to work out exactly what the cross-sections in table 4 of the above AN mean. One way to do that is to attempt to replicate them with known, explicit configuration. Let's first try to replicate the first line which is:

  `TTbarDMJets_scalar_Mchi-1_Mphi-10_TuneCUETP8M1_13TeV-madgraphMLM-pythia8 | 21.36 [pb]`

  - Tried looking on DIS for the configuration that was used for this dataset explicitly and came up empty (couldn't find parent dataset... or something).
  - Instead, just look in `genproductions` and guess which is the correct one to use. Let's try [this one](https://github.com/cms-sw/genproductions/blob/02c6e5b080dc6e6a5d9ab8fb16b793505262e14d/bin/MadGraph5_aMCatNLO/cards/production/13TeV/DarkMatter/DMScalar_ttbar/DMScalar_ttbar01j_mphi_10_mchi_1_gSM_1p0_gDM_1p0/DMScalar_ttbar01j_mphi_10_mchi_1_gSM_1p0_gDM_1p0_proc_card.dat).

-> DMScalar_ttbar01j_mphi_10_mchi_1_gSM_1p0_gDM_1p0_proc_card.dat
```
#************************************************************
#*                        MadGraph 5                        *
#*                                                          *
#*                *                       *                 *
#*                  *        * *        *                   *
#*                    * * * * 5 * * * *                     *
#*                  *        * *        *                   *
#*                *                       *                 *
#*                                                          *
#*                                                          *
#*    The MadGraph Development Team - Please visit us at    *
#*    https://server06.fynu.ucl.ac.be/projects/madgraph     *
#*                                                          *
#************************************************************
#*                                                          *
#*               Command File for MadGraph 5                *
#*                                                          *
#*     run as ./bin/mg5  filename                           *
#*                                                          *
#************************************************************
import model DMScalar_ttbar01j_gSM_1p0_gDM_1p010_mchi_1_gSM_1p0_gDM_1p0
# Define multiparticle labels
define p = g u c d s u~ c~ d~ s~
define j = g u c d s u~ c~ d~ s~
define l+ = e+ mu+
define l- = e- mu-
define vl = ve vm vt
define vl~ = ve~ vm~ vt~
# Specify process(es) to run
#generate p p > t t~ chi chi~

generate p p > t t~ chi chi~ @0
add process  p p > t t~ chi chi~ j @1
#add process  p p > t t~ chi chi~ j j @2
# KH, phim is implicit.  MadSpin chokes if explicit

#generate p p > t t~ phim, (phim > chi chi~) @0
#add process p p > t t~ phim j, (phim > chi chi~) @1
#add process p p > t t~ phim j j, (phim > chi chi~) @2


# Output processes to MadEvent directory
output
# This will create a directory PROC_$MODELNAME_$X
# If you want to specify the path/name of the directory use
output DMScalar_ttbar01j_mphi_10_mchi_1_gSM_1p0_gDM_1p0

# To generate events, you can go to the created directory and
# run ./bin/generate_events
```

  - So, it looks like the process being considered is proton-proton to ttbar + chichibar + 0 or 1 extra jet. Let's see if this produces numbers like in the table.
  - The model crashes with a modern version of Madgraph (2.6.X), but the AN says it was used in version 2.2.2. Sadly, this version is not an available release on the Madgraph5_aMC launchpad page. However, 2.2.3 is. A quick test with this release confirmed that the model runs in this version.
  - To help with future efforts that may require cross-version studies, I implemented code to query launchpad for all releases, and then automatically download, install, and configure them upon request with the --mg flag. Frankly, this was probably overkill, but whatever.
