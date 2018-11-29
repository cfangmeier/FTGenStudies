# set -e
model="Zprime_UFO"
proj="ZPrimeStudies"

# NOTE: Default zprime params
# BLOCK ZPRIME # 
#       1 1.000000e+00 # gt
#       2 0.000000e+00 # al
#       3 1.000000e+00 # ar

# ./run.py $proj --model $model -p tttt_fixedorder_lo \
#     --mass zp:25,50,75,100,125,175 \
#     --param ZPRIME:1:0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0,1.1,1.2,1.3,1.4,1.5

proj="ZPrimeCrosscheck"
./run.py $proj --model Zprime_UFO -p tttt_lo tttt_nlo --param ZPRIME:1:0.0
./run.py $proj --model sm -p tttt_lo tttt_nlo

