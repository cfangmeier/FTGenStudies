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

  - Comparing cross-section for the case M_phi=50GeV, M_chi=1GeV, the naive run gives a cross-section of 69.36pb while the paper quotes 3.088 (69.36/3.088=22.46). A more thorough comparison is listed in the table below:

```
Model       m_{chi}  m_{phi}    xs_paper     xs_mine     pap/me   me/pap
DMPseudo          1       10   0.45170000  19.11000000   0.0236  42.3068
DMPseudo          1       20   0.41170000  15.55000000   0.0265  37.7702
DMPseudo          1      100   0.19320000   5.65400000   0.0342  29.2650
DMPseudo          1      200   0.08786000   2.36600000   0.0371  26.9292
DMPseudo          1      300   0.03950000   1.14600000   0.0345  29.0127
DMPseudo          1      500   0.00516300   0.12630000   0.0409  24.4625
DMPseudo         10       10   0.01522000   5.77500000   0.0026 379.4350
DMPseudo         10      100   0.19760000   5.67800000   0.0348  28.7348
DMPseudo         50       10   0.00240500   1.00500000   0.0024 417.8794
DMPseudo         50      200   0.08476000   2.36100000   0.0359  27.8551
DMPseudo         50      300   0.03845000   1.12400000   0.0342  29.2328

DMScalar          1       10  21.36000000 549.00000000   0.0389  25.7022
DMScalar          1       20  10.95000000 266.60000000   0.0411  24.3470
DMScalar          1      100   0.72050000  15.71000000   0.0459  21.8043
DMScalar          1      200   0.10160000   2.49100000   0.0408  24.5177
DMScalar          1      300   0.03045000   0.85950000   0.0354  28.2266
DMScalar          1      500   0.00494700   0.14020000   0.0353  28.3404
DMScalar         10       10   0.10110000  32.99000000   0.0031 326.3106
DMScalar         10      100   0.74170000  15.55000000   0.0477  20.9653
DMScalar         50       10   0.00207800   0.72000000   0.0029 346.4870
DMScalar         50      200   0.10030000   2.34200000   0.0428  23.3500
DMScalar         50      300   0.03046000   0.79070000   0.0385  25.9586
```

  - So my numbers are tending to be something like 20-40x larger than those in the paper (not counting the few cases where my numbers are ~300-400x larger). Clearly somethings isn't matching up.

  - For reference, here is one of my proc_cards (compare with above)

```
#************************************************************
#*                     MadGraph5_aMC@NLO                    *
#*                                                          *
#*                *                       *                 *
#*                  *        * *        *                   *
#*                    * * * * 5 * * * *                     *
#*                  *        * *        *                   *
#*                *                       *                 *
#*                                                          *
#*                                                          *
#*         VERSION 2.2.3                 2015-02-10         *
#*                                                          *
#*    The MadGraph5_aMC@NLO Development Team - Find us at   *
#*    https://server06.fynu.ucl.ac.be/projects/madgraph     *
#*                                                          *
#************************************************************
#*                                                          *
#*               Command File for MadGraph5_aMC@NLO         *
#*                                                          *
#*     run as ./bin/mg5_aMC  filename                       *
#*                                                          *
#************************************************************
set group_subprocesses Auto
set ignore_six_quark_processes False
set loop_optimized_output True
set complex_mass_scheme False
import model DMScalar
define p = g u c d s u~ c~ d~ s~
define j = g u c d s u~ c~ d~ s~
define l+ = e+ mu+
define l- = e- mu-
define vl = ve vm vt
define vl~ = ve~ vm~ vt~
define p = p b b~
define j = p
generate p p > t t~ chi chi~
add process p p > t t~ chi chi~ j
output runs/DM/13p0_phi10000p0chi10p0_calar__ttchichiets_/
```