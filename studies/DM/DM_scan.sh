
python ft_tools/run.py DM --model DMScalar \
                          --proc ttchichi --proc ttchichiJets \
                          --condor \
                          --mg 2_2_3 \
                          --mass phi:10,20,50,100,200,300,500,10000 \
                          --mass chi:1,10,50 \
                          --noprompt

python ft_tools/run.py DM --model DMPseudo \
                          --proc ttchichi --proc ttchichiJets \
                          --condor \
                          --mg 2_2_3 \
                          --mass phi:10,20,50,100,200,300,500,10000 \
                          --mass chi:1,10,50 \
                          --noprompt
