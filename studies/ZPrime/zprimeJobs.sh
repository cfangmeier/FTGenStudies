# set -e
proj="ZPrimeStudies_QED2"

# NOTE: Default zprime params
# BLOCK ZPRIME # 
#       1 1.000000e+00 # gt
#       2 0.000000e+00 # al
#       3 1.000000e+00 # ar

python ft_tools/run.py $proj \
    --model Zprime_UFO \
    --proc "tttt:QED=2" \
    --mass zp:25,50,75,100,125,175 \
    --param ZPRIME:1:0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0,1.1,1.2,1.3,1.4,1.5 \
    --ncore 2 \
    --condor


# python ft_tools/run.py $proj \
#     --model Zprime_UFO \
#     --proc "tttt:QED=2" \
#     --mass zp:25 \
#     --param ZPRIME:1:0.0,0.1,0.2,0.3 \
#     --condor
