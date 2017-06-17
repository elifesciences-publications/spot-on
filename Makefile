# A simple Makefile for Spot-On
# This file is part of the Spot-On program
# By MW, AGPLv3+
# This provides some installation/init shortcuts to be run after downloading
# all the libraries

ABPARAMS_URL="http://alineos2-darzacqlab.mcb.berkeley.edu:8000/static/SPTGUI/"
ABPARAMS_FNM="170614_fitted_abParams.bz2"
EXAMPLDTA_URL=${ABPARAMS_URL}
EXAMPLDTA_FNM="170616_demoFiles.tar.bz2"

# init does the following:
#+ 1. Download (a,b) coefficients for the corrected z depth
#+ 2. Create an empty database
#+ 3. Download example dataset
#+ 4. Create the demo dataset

.PHONY: init
init:
	echo "-- 1. Download (a,b) coefficients for the corrected z depth"
	wget ${ABPARAMS_URL}${ABPARAMS_FNM}
	cd SPTGUI/;tar xvjf ../${ABPARAMS_FNM}

	echo "-- 2. Creating an empty database"
	python manage.py migrate

	echo "-- 3. Downloading example dataset"
	wget ${EXAMPLDTA_URL}${EXAMPLDTA_FNM}
	tar xvjf ${EXAMPLDTA_FNM}

	echo "-- 4. Creating folder architecture"
	mkdir -p static/upload/
	mkdir    static/tmpdir/
	mkdir    static/analysis
	mkdir -p uploads/uploads/

	echo "-- 5. Populating the database"
	python demofiles.py

	echo "-- 6. Editing custom_settings.py"
	sed -i.bak 's/use_demo = False/use_demo = True/g' fastSPT/custom_settings.py
	sed -i.bak 's/demo_id = None/demo_id = '`cat .id`'/g' fastSPT/custom_settings.py

.PHONY: clean
clean:
	echo "-- 1. Deleting the database"
	rm db.sqlite3

	echo "-- 2. Deleting the (a,b) coefficients"
	rm -rf SPTGUI/fit_zcorr/

	echo "-- 3. Deleting the uploaded folders"
	rm uploads/*
	rm uploads/uploads/*
	rm static/upload/*
	rm -rf static/analysis/*
