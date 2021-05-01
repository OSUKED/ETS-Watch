call cd ..
call conda activate etswatch
call python setup.py sdist bdist_wheel
call twine upload --skip-existing dist/*
pause