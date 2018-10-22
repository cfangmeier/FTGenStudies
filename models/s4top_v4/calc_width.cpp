#include <fstream>
#include <iostream>
#include <cstdlib> 
#include <math.h>
#include <string>
#include <algorithm>
#include <vector>
#include <stdlib.h>
#include <stdio.h>
using namespace std;
int main(int argc, char* argv[])
{
	ofstream o("param_card.dat");
	const double mt=173.2,pi=4.0*atan(1.0),mz=91.1876,mw=80.385,alpha=1.0/132.233230;
	double ms,gc,wdh,wda,r,mtMS,yt,v;
	ms=strtod(argv[1], NULL);
	gc=strtod(argv[2], NULL);
	v=2.0*mw*sqrt(1.0-pow(mw/mz,2))/sqrt(4.0*pi*alpha);
	mtMS=160.0;
	yt=mtMS/v;
	r=mt*mt/ms/ms;
	wdh=3.0*yt*yt*gc*gc*ms/(8.0*pi)*pow(1.0-4.0*r,1.5);
	wda=3.0*yt*yt*gc*gc*ms/(8.0*pi)*sqrt(1.0-4.0*r);
	o<<"#******************************************************************"<<endl;
	o<<"#                      MadGraph/MadEvent                          *"<<endl;
	o<<"#******************************************************************"<<endl;
	o<<"#   Les Houches friendly file for the SM parameters of MadGraph   *"<<endl;
	o<<"#        Spectrum and decay widths produced by SMCalc             *"<<endl;
	o<<"#******************************************************************"<<endl;
	o<<"#*Please note the following IMPORTANT issues:                     *"<<endl;
	o<<"#                                                                 *"<<endl;
	o<<"#0. REFRAIN from editing this file by hand! Some of the parame-   *"<<endl;
	o<<"#   ters are not independent                                      *"<<endl;
	o<<"#   (such as G_Fermi, alpha_em, sin(theta_W),MZ,MW) and serious   *"<<endl;
	o<<"#   problems might be encountered (such as violation of unitarity *"<<endl;
	o<<"#   or gauge invariance).  Always use a calculator.               *"<<endl;
	o<<"#                                                                 *"<<endl;
	o<<"#1. alpha_S(MZ) has been used in the calculation of the parameters*"<<endl;
	o<<"#   but, for consistency, it will be reset by madgraph to the     *"<<endl;
	o<<"#   value expected IF the pdfs for collisions with hadrons are    *"<<endl;
	o<<"#   used. This value is KEPT by madgraph when no pdf are used     *"<<endl;
	o<<"#   lpp(i)=0 .                                                    *"<<endl;
	o<<"#                                                                 *"<<endl;
	o<<"#2. Values of the charm and bottom kinematic (pole) masses are    *"<<endl;
	o<<"#   those used in the matrix elements and phase space UNLESS they *"<<endl;
	o<<"#   are set to ZERO from the start in the model (particles.dat)   *"<<endl;
	o<<"#   This happens, for example,  when using 5-flavor QCD where     *"<<endl;
	o<<"#   charm and bottom are treated as partons in the initial state  *"<<endl;
	o<<"#   and a zero mass might be hardwired in the model definition.   *"<<endl;
	o<<"#                                                                 *"<<endl;
	o<<"#******************************************************************"<<endl;
	o<<"Block SMINPUTS      # Standard Model inputs"<<endl;
	o<<"     1         1.32233230E+02   # alpha_em(MZ)(-1) SM MSbar"<<endl;
	o<<"     2         1.16637870E-05   # G_Fermi"<<endl;
	o<<"     3         1.18000000E-01   # alpha_s(MZ) SM MSbar"<<endl;
	o<<"     4         9.11876000E+01   # Z mass (as input parameter)"<<endl;
	o<<"Block MGYUKAWA     # Yukawa masses m/v=y/sqrt(2)"<<endl;
	o<<"#    PDG          YMASS"<<endl;
	o<<"     5         4.18000000E+00   # mbottom for the Yukawa  y_b"<<endl;
	o<<"     4         1.42000000E+00   # mcharm  for the Yukawa  y_c"<<endl;
	o<<"     6         1.63000000E+02   # mtop    for the Yukawa  y_t"<<endl;
	o<<"    15         1.77700000E+00   # mtau    for the Yukawa  y_ta"<<endl;
	o<<"Block MGCKM     # CKM elements for MadGraph"<<endl;
	o<<"     1   1     9.75000000E-01   # Vud for Cabibbo matrix"<<endl;
	o<<"#==========================================================="<<endl;
	o<<"# QUANTUM NUMBERS OF NEW STATE(S) (NON SM PDG CODE) IF ANY"<<endl;
	o<<"# (see below for masses and decay tables)"<<endl;
	o<<"# These blocks are automatically created by the MadGraph"<<endl;
	o<<"# qnumbers.pl script from the particles.dat model file"<<endl;
	o<<"#==========================================================="<<endl;
	o<<"# END of QNUMBERS blocks"<<endl;
	o<<"#==========================================================="<<endl;
	o<<"#==========================================================="<<endl;
	o<<"# QUANTUM NUMBERS OF NEW STATE(S) (NON SM PDG CODE) IF ANY"<<endl;
	o<<"# (see below for masses and decay tables)"<<endl;
	o<<"# These blocks are automatically created by the MadGraph"<<endl;
	o<<"# qnumbers.pl script from the particles.dat model file"<<endl;
	o<<"#==========================================================="<<endl;
	o<<"# END of QNUMBERS blocks"<<endl;
	o<<"#==========================================================="<<endl;
	o<<"Block MASS      #  Mass spectrum (kinematic masses)"<<endl;
	o<<"#       PDG       Mass"<<endl;
	o<<"         5     4.78000000E+00   # bottom   pole mass"<<endl;
	o<<"         6     1.73200000E+02   # top      pole mass"<<endl;
	o<<"        15     1.77700000E+00   # tau      mass"<<endl;
	o<<"        23     9.11876000E+01   # Z        mass"<<endl;
	o<<"        24     8.03850000E+01   # W        mass"<<endl;
	o<<"        25     1.25000000E+02   # H        mass"<<endl;
	o<<"        35     "<<ms<<"   # H2MASS"<<endl;
	o<<"        36     "<<ms<<"   # A2MASS"<<endl;
	o<<"#            PDG       Width"<<endl;
	o<<"DECAY        35     "<<wdh<<"   # H2WIDTH"<<endl;
	o<<"DECAY        36     "<<wda<<"   # A2WIDTH"<<endl;
	o<<"DECAY         6     1.47537201E+00   # top width"<<endl;
	o<<"DECAY        23     2.43945694E+00   # Z   width"<<endl;
	o<<"DECAY        24     2.04498331E+00   # W   width"<<endl;
	o<<"DECAY        25     6.34327597E-03   # H   width"<<endl;
	o<<"#        BR           NDA        ID1       ID2"<<endl;
	o<<"     7.81775613E-02    2           4        -4   # BR( H -> c  cbar  )"<<endl;
	o<<"     6.71990833E-01    2           5        -5   # BR( H -> b  bbar  )"<<endl;
	o<<"     0.00000000E+00    2           6        -6   # BR( H -> t  tbar  )"<<endl;
	o<<"     4.07905119E-02    2          15       -15   # BR( H -> tau- tau+)"<<endl;
	o<<"     1.33251814E-02    2          23        23   # BR( H -> Z   Z^(*))"<<endl;
	o<<"     1.22631092E-01    2          24       -24   # BR( H -> W   W^(*))"<<endl;
	o<<"     3.07534079E-02    2          21        21   # BR( H -> g   g    )"<<endl;
	o<<"     1.54090058E-03    2          22        22   # BR( H -> A   A    )"<<endl;
	o<<"BLOCK MGUSER"<<endl;
	o<<"         1     "<<gc<<"   # gch ,first variable name"<<endl;
	o<<"         2     "<<gc<<"   # gca ,second variable name"<<endl;
	o.close();
	return 0;
}