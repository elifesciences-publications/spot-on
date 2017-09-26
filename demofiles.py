# Script that imports the demo files to a the database
# MW, GPLv3+, Jun. 2017
# This script does:
# 1. Creates an analysis called demo{n}
#    (where n gets incremented as new demo are created)
# 2. Imports all the .mat files in the demofiles/ folder
# 3. Sets the SPOTON_DEMOID environment variable
# 4. Returns the id of the Analysis created (so that you can update your
#    custom_settings.py file
# /!\ Some important parameters might also be in the `SPTGUI/import_tools.py` file

## ==== Variables
bn = "demofiles/"

## ==== Imports
import os, sys
import django
from django.utils import timezone
from django.core.files import File

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fastSPT.settings")
django.setup()

from SPTGUI.models import Analysis
import SPTGUI.import_tools as import_tools

## ==== Functions
def get_demo_name():
    ok = False
    i=0
    while not ok:
        name = "demo{}".format(i)
        if len(Analysis.objects.filter(url_basename=name))==0:
            ok = True
            break
        i+=1
    return name

## ==== Main
if __name__=='__main__':
    bf="./static/analysis/"

    ## Scan the folder
    print "-- Scanning {}".format(bn)
    df = [i for i in os.listdir(bn) if i.endswith(".mat")]
    print "Found {} files ending with .mat in {}".format(len(df), bn)

    ## Create the analysis
    url_basename = get_demo_name()
    print "-- Creating analysis {}".format(url_basename)
    ana = Analysis(url_basename=url_basename,
                   pub_date=timezone.now(),
                   name='',
                   description='Demo analysis',
                   editable = False)
    ana.save()
    if not os.path.isdir(bf+url_basename):
        os.makedirs(os.path.join(bf,url_basename))
    print "Analysis created"

    ## Import the datasets
    print "-- Importing datasets"
    for (i,name) in enumerate(df):
        print "Importing dataset {}/{}".format(i+1, len(df))
        path = os.path.join(bn, name)
        
        ## Create a file object
        fi = File(open(path, 'r'))
        fi.name = name
        
        import_tools.import_dataset(fi, name, ana, url_basename, bf=bf, fmt="anders")

    ## Exiting
    print "All done, the id of the Analysis database is {}".format(ana.id)
