# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task

import os, sys, tempfile, json, pickle, fasteners
import numpy as np
## Initialize django stuff
import django
django.setup()

from django.core.files import File
from SPTGUI.models import Dataset
import SPTGUI.parsers as parsers

sys.path.append('SPTGUI/fastSPT_analysis')
import fastSPT_analysis as fastSPT

##
## ==== Here go the tasks to be performed asynchronously
##    

@shared_task
def compute_jld(dataset_id):
    """This function computes the histogram of jump length of an uploaded 
    dataset and save it in the corresponding dataset slot. It does not 
    compute the fit of the dataset."""

    ## ==== Perform analysis
    print "Computing JLD for dataset {}".format(dataset_id)

    da = Dataset.objects.get(id=dataset_id)
    with open(da.parsed.path, 'r') as f:  ## Open dataset
        cell = parsers.to_fastSPT(f) ## Format the dataset for analysis
        print "WARNING, using default parameters to compute jld"
        an = fastSPT.compute_jump_length_distribution(cell, CDF=True, useAllTraj=True) ## Perform the analysis

    print "DONE: Computed JLD for dataset {}".format(dataset_id)
        
    ## ==== Save results
    with tempfile.NamedTemporaryFile(dir="static/upload/", delete=False) as f:
        fil = File(f)
        pickle.dump(an, fil) #fil.write(json.dumps(fi))
        da.jld = fil
        da.jld.name = da.data.name + '.jld'
        da.save()    


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

    
    ## ==== Load JLD
    da =  Dataset.objects.get(id=dataset_id)
    with open(da.jld.path, 'r') as f: ## Open the pickle file
        jld = pickle.load(f)
        HistVecJumps = jld[2] ## Extract from the pickled file
        JumpProb = jld[3]
        HistVecJumpsCDF = jld[0]
        JumpProbCDF = jld[1]        
    
    ## ==== Initialize
    with fasteners.InterProcessLock(prog_p+'.lock'):
        with open(prog_p, 'r') as f:
            save_pars = pickle.load(f)
            save_pars['queue'][dataset_id]['status'] = 'processing'
        with open(prog_p, 'w') as f:
            pickle.dump(save_pars, f)

    ## ==== Sanity format the dictionary of parameters
    params = save_pars['pars'].copy()
    params.pop("include")
    params.pop("hashvalue")
    params["D_Bound"] = params.pop("D_bound")
    params["D_Free"] = params.pop("D_free")
    params["Frac_Bound"] = params.pop("F_bound")
    print params
    
    ## ==== Perform the fit and compute the distribution
    fit = fastSPT.fit_jump_length_distribution(JumpProb, JumpProbCDF,
                                               HistVecJumps, HistVecJumpsCDF,
                                               **params)
    ## Generate the PDF corresponding to the fitted parameters
    y = fastSPT.generate_jump_length_distribution(fit.params['D_free'],
                                                  fit.params['D_bound'],
                                                  fit.params['F_bound'],  
                                                  JumpProb,
                                                  HistVecJumpsCDF,
                                                  params['LocError'],
                                                  params['dT'],
                                                  params['dZ'])
    ## Normalize it
    norm_y = np.zeros_like(y)
    for i in range(y.shape[0]): # Normalize y as a PDF
        norm_y[i,:] = y[i,:]/y[i,:].sum()
        scaled_y = (float(len(HistVecJumpsCDF))/len(HistVecJumps))*norm_y
    
    # ==== Save results
    ## Save the histogram (save params AND the hist)
    prog_da = os.path.join(path,url_basename, "{}_{}.pkl".format(hash_prefix,
                                                                     dataset_id))
    with fasteners.InterProcessLock(prog_da+'.lock'):
        with open(prog_da, 'w') as f:
            pickle.dump({'fit': scaled_y,
                         'fitparams': fit.params,
                         'params' : save_pars['pars']}, f)
    
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

    return file_id
