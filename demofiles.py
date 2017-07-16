# Script that imports the demo files to a the database
# MW, GPLv3+, Jun. 2017
# This script does:
# 1. Creates an analysis called demo{n}
#    (where n gets incremented as new demo are created)
# 2. Imports all the .mat files in the demofiles/ folder
# 3. Sets the SPOTON_DEMOID environment variable
# 4. Returns the id of the Analysis created (so that you can update your
#    custom_settings.py file

## ==== Variables
bn = "demofiles/"

## ==== Imports
import os, sys, pickle
import django
from django.utils import timezone
from django.core.files import File

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fastSPT.settings")
django.setup()

from SPTGUI.models import Analysis, Dataset
import fastSPT.custom_settings as custom_settings
import SPTGUI.tasks as tasks

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

def import_dataset(path, name, ana, url_basename):
    ## Variables
    fmt="anders"
    fmtParams = {}
    
    ## Create a file object
    fi = File(open(path, 'r'))
    fi.name = name

    ## Create the dataset
    da = Dataset(analysis=ana,
                 name=name,
                 description='Demo dataset',
                 unique_id = 0,
                 upload_status=True, # Upload is complete
                 preanalysis_status='uploaded', # Preanalysis not launched
                 data=fi)
    da.save()

    ## Precompute JLD
    compute_params = custom_settings.compute_params
    pick = {'params' : compute_params,
            'jld' : None,
            'status' : 'queued'}
    cha = "03f9de26788d1c29" #'c0f7e565600c3bf5'
    pa = bf+"{}/jld_{}_{}.pkl".format(url_basename, cha, da.id)
    with open(pa, 'w') as f: ## Save that we are computing
        pickle.dump(pick, f)
    tasks.check_input_file(da.data.path, da.id, fmt, fmtParams, queue=False)
    tasks.compute_jld(da.id,
                      pooled=False,
                      path=bf,
                      hash_prefix=cha,
                      compute_params=compute_params,
                      url_basename=url_basename,
                      default=True, queue=False)

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
        import_dataset(path, name, ana, url_basename)

    ## Exiting
    print "All done, the id of the Analysis database is {}".format(ana.id)
