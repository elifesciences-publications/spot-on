## A simple test suite to be run standalone to test the statistics module.
## By MW, Apr. 2017
## GPLv3+
##
## This is how it work:
## - It takes all the datasets in the database
## - And apply all the functions of the statistics.py to the parsed dataset.
## - And displays a pretty report (in theory).

## ==== Imports
from __future__ import absolute_import, unicode_literals
import json, os

import SPTGUI.statistics as stats
from SPTGUI.models import Dataset, Analysis


## ==== The main function
def tests(fi):
    stats.number_of_trajectories(fi) # number of traces
    stats.number_of_detections(fi)   # number of points
    le = stats.length_of_trajectories(fi)
    #le["median"]
    #le["mean"]
    le = stats.particles_per_frame(fi)
    #le["median"]
    #le["mean"]
    stats.number_of_trajectories3(fi)
    stats.number_of_jumps(fi)
    stats.jump_length(fi)
    
def test_statistics():
    for ana in Analysis.objects.all():
        print "---- {}".format(ana.url_basename)
        for da in Dataset.objects.filter(analysis=ana):
            print "-- new dataset {}".format(da.id)
            if not check_jld(da):
                print "/!\ dataset not found"
            else:
                with open(da.parsed.path, 'r') as f:
                    fi = json.load(f)
                    tests(fi)

def check_jld(d):
    """Small helper function to check if we have a JLD stored"""
    try:
        return os.path.exists(d.jld.path)
    except:
        return False

        

## ==== Run it standalone
if __name__ == '__main__':
    print "Running tests to assess the quality of our statistics"
    test_statistics()
