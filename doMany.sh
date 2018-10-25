hdm_model="s4top_v4"
proj="2HDMTesting_s4top"

# p p > t t~ h1/2 with default settings
./run.py $proj --model $hdm_model -p tth_lo tth2_lo --noprompt --nokeep

# p p > t t~ h for comparison with sm result
./run.py $proj --model sm -p tth_lo --mass h:125 --noprompt

# # p p > t t~ h1/2 with equal masses
# ./run.py $proj --model $hdm_model -p tth1_lo tth2_lo --mass h:125 --mass h2:125 --noprompt
# ./run.py $proj --model $hdm_model -p tth1_lo tth2_lo --mass h:150 --mass h2:150 --noprompt
# ./run.py $proj --model $hdm_model -p tth1_lo tth2_lo --mass h:350 --mass h2:350 --noprompt
# ./run.py $proj --model $hdm_model -p tth1_lo tth2_lo --mass h:450 --mass h2:450 --noprompt

# # p p > t t~ h1/2 with fixed h1 mass and varying h2 mass
# ./run.py $proj --model $hdm_model -p tth1_lo tth2_lo --mass h:125 --mass h2:100 --noprompt
# ./run.py $proj --model $hdm_model -p tth1_lo tth2_lo --mass h:125 --mass h2:200 --noprompt
# ./run.py $proj --model $hdm_model -p tth1_lo tth2_lo --mass h:125 --mass h2:300 --noprompt
# ./run.py $proj --model $hdm_model -p tth1_lo tth2_lo --mass h:125 --mass h2:400 --noprompt
# ./run.py $proj --model $hdm_model -p tth1_lo tth2_lo --mass h:125 --mass h2:500 --noprompt
# ./run.py $proj --model $hdm_model -p tth1_lo tth2_lo --mass h:125 --mass h2:600 --noprompt
# # p p > t t~ h1/2 with fixed h2 mass and varying h1 mass
# ./run.py $proj --model $hdm_model -p tth1_lo tth2_lo --mass h:100 --mass h2:125 --noprompt
# ./run.py $proj --model $hdm_model -p tth1_lo tth2_lo --mass h:200 --mass h2:125 --noprompt
# ./run.py $proj --model $hdm_model -p tth1_lo tth2_lo --mass h:300 --mass h2:125 --noprompt
# ./run.py $proj --model $hdm_model -p tth1_lo tth2_lo --mass h:400 --mass h2:125 --noprompt
# ./run.py $proj --model $hdm_model -p tth1_lo tth2_lo --mass h:500 --mass h2:125 --noprompt
# ./run.py $proj --model $hdm_model -p tth1_lo tth2_lo --mass h:600 --mass h2:125 --noprompt

# # p p > t t~ h1/2 with h1 huge mass
# ./run.py $proj --model $hdm_model -p tth1_lo tth2_lo --mass h:2000 --noprompt
# # p p > t t~ h1/2 with h2 huge mass
# ./run.py $proj --model $hdm_model -p tth1_lo tth2_lo --mass h2:2000 --noprompt


# # p p > t t~ h1/2, h1/2 > b b~ for comparison w/ sm
# ./run.py $proj --model $hdm_model -p tthxbb_lo --mass h:125 --mass h2:125 --noprompt
# ./run.py $proj --model sm -p tthbb_lo --mass h:125 --noprompt
