# A simple Makefile for Spot-On
# This file is part of the Spot-On program
# By MW, AGPLv3+
# This provides some installation/init shortcuts to be run after downloading
# all the libraries

ABPARAMS_URL="http://alineos2-darzacqlab.mcb.berkeley.edu:8000/static/SPTGUI/"
ABPARAMS_FNM="170614_fitted_abParams.bz2"

# init does the following:
#+ 1. Download (a,b) coefficients for the corrected z depth
#+ 2. Create an empty database
#+ 3. Download example dataset
#+ 4. Create the demo dataset

.PHONY: init
init:
	echo "1. Download (a,b) coefficients for the corrected z depth"
	wget ${ABPARAMS_URL}${ABPARAMS_FNM}
	cd SPTGUI/;tar xvjf ${ABPARAMS_FNM}

	echo "2. Creating an empty database"
