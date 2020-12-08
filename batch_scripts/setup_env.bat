call cd ..
call conda env create -f environment.yml
call conda activate ETSWatch
call ipython kernel install --user --name=ETSWatch
pause