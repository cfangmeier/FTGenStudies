# p p > t t~ h1/2 with default settings
./run.py 2HDMTesting --model 2HDM -p tth1_lo tth2_lo --noprompt --nokeep
# p p > t t~ h1/2 with equal masses
./run.py 2HDMTesting --model 2HDM -p tth1_lo tth2_lo --mass h1:125 --mass h2:125 --noprompt
# p p > t t~ h1/2 with h1 huge mass
./run.py 2HDMTesting --model 2HDM -p tth1_lo tth2_lo --mass h1:2000 --noprompt
# p p > t t~ h1/2 with h2 huge mass
./run.py 2HDMTesting --model 2HDM -p tth1_lo tth2_lo --mass h2:2000 --noprompt
