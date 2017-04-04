# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task

import os, sys, tempfile, json, pickle, fasteners
## Initialize django stuff
import django
django.setup()

from django.core.files import File
from SPTGUI.models import Dataset
import SPTGUI.parsers as parsers

sys.path.append('fastSPT')
import fastSPT

##
## ==== Here go the tasks to be performed asynchronously
##    

@shared_task
def fit_jld(path, url_basename, hash_prefix, dataset_id):
    """This function fits the histogram of jump lengths of a given 
    dataset for a specific set of parameters to a BOUND-UNBOUND kinetic 
    model.
    
    Inputs:
    - path: the folder where the analyses are stored
    - url_basename: the name of the analysis page
    - hash_prefix: the prefix filename
    - dataset_id: the id of the dataset in the database.

    Returns: None
    - Update the Dataset entry with the appropriately parsed information
    """
    prog_p = os.path.join(path,url_basename, "{}_progress.pkl".format(hash_prefix))

    ## === Initialize
    with fasteners.InterProcessLock(prog_p+'.lock'):
        with open(prog_p, 'r') as f:
            save_pars = pickle.load(f)
            save_pars['queue'][dataset_id]['status'] = 'processing'
        with open(prog_p, 'w') as f:
            pickle.dump(save_pars, f)

    ## ==== Perform analysis
    da = Dataset.objects.get(id=dataset_id)
    with open(da.parsed.path, 'r') as f:  ## Open dataset
        fastSPT
        ## Format the dataset for analysis
        ## Perform the analysis
        ## Save the corresponding file

    # ==== Save results
    ## Save the histogram (save params AND the hist)
    
    ## Open the pickle file and change the pickle file to 'done'
    with fasteners.InterProcessLock(prog_p+'.lock'):
        with open(prog_p, 'r') as f:
            save_pars = pickle.load(f)
        save_pars['queue'][dataset_id]['status'] = 'done'
        with open(prog_p, 'w') as f:
            pickle.dump(save_pars, f)
    
@shared_task
def check_input_file(filepath, file_id):
    """This function checks that the uploaded file has the right format and
    can be analyzed. It is further saved in the database
    
    Inputs:
    - filepath: the path to the file to be checked
    - file_id: the id of the file in the database.

    Returns: None
    - Update the Dataset entry with the appropriately parsed information
    """
    
    ## ==== Sanity checks
    da = Dataset.objects.get(id=file_id)
    
    ## ==== Check file format
    try: # try to parse the file
        fi = parsers.read_file(da.data.path)
    except: # exit
        da.preanalysis_token = ''
        da.preanalysis_status = 'error'
        da.save()
        return

    ## ==== Save the parsed result!
    with tempfile.NamedTemporaryFile(dir="static/upload/", delete=False) as f:
        fil = File(f)
        fil.write(json.dumps(fi))

        da.parsed = fil
        da.parsed.name = da.data.name + '.parsed'
        da.save()

    ## ==== Extract the relevant information
    da.pre_ntraces = len(fi) # number of traces
    da.pre_npoints = sum([len(i) for i in fi]) # number of points

    ## ==== Update the state
    da.preanalysis_token = ''
    da.preanalysis_status = 'ok'
    da.save()
