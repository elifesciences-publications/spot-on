# Index of views for the fastSPT-GUI app
# A graphical user interface to the fastSPT tool by Anders S. Hansen, 2016
# By MW, GPLv3+, Feb.-Apr. 2017
#
# Here we store views that relate to the upload of datasets

## ==== Imports
import os, json, pickle, re
import fileuploadutils2 as fuu
from django.http import HttpResponse
from flask import Response
from .models import Analysis, Dataset
from django.core.files import File
import celery, tasks
from django.utils import timezone

bf = "./static/analysis/" ## Location to save the fitted datasets


## ==== Views
def upload(request, url_basename):
    """A backend for the upload debugging stuff"""
    ## Call the original stuff
    ## Make sure we send the right stuff back.
    resp=Response()
    resp.ok = False
	
    filename=None
    responseTotalChunks=None
    """
    flow js always send a get befora a post, the first
    one give some information for the program to use to
    build the file when the upload is finished
    """
    # Format the request object

    request.args = request.GET
    try:
        request.form = request.POST
    except:
        request.form = []

    fuu.chunkOperationUtil(request,resp);

    # Transfer to a real object
    res = HttpResponse()
    res.content = resp.data
    res.status_code = int(resp.status)

    if res.status_code == 200 and resp.ok:
        ## 1. Get the analysis object, or create it if it doesn't exist
        try:
            ana = Analysis.objects.get(url_basename=url_basename)
        except:
            if re.match('^[\w-]+$', url_basename) is None: ## contains non allowed chars
                logging.error("tried to create an analyis with non-allowed characters in the name")
                return "character not allowed"
            
                
            ana = Analysis(url_basename=url_basename,
                           pub_date=timezone.now(),
                           name='',
                           description='')
            ana.save()
            os.makedirs(bf+url_basename) # Create folder for analyses


        ## 2. Create a database entry
        fi = File(open(json.loads(res.content)['address'], 'r')) ## This could be handled differently
        fi.name = json.loads(res.content)['filename']
        da = Dataset(analysis=ana,
                     name=request.POST['flowFilename'],
                     description='',
                     unique_id = json.loads(res.content)['unique_id'],
                     upload_status=True, # Upload is complete
                     preanalysis_status='uploaded', # Preanalysis not launched
                     data=fi)
        da.save()

        ## 3. Defer to the celery analysis
        ## Here we first perform the "check_input_file" task. If this one returns
        ## properly, the histogram of jump lengths distribution is computed
        ## (compute_jld).
        compute_params = {'BinWidth' : 0.01,
                          'GapsAllowed' : 1,
                          'TimePoints' : 8,
                          'JumpsToConsider' : 4,
                          'MaxJump' : 1.25,
                          'TimeGap' : 4.477}
        pick = {'params' : compute_params,
                'jld' : None,
                'status' : 'queued'}
        cha = 'c0f7e565600c3bf5'
        pa = bf+"{}/jld_{}_{}.pkl".format(url_basename, cha, da.id)
        with open(pa, 'w') as f: ## Save that we are computing
            pickle.dump(pick, f)
        
        da.preanalysis_status='queued'
        ta = tasks.check_input_file.apply_async(
            (da.data.path, da.id),
            link=tasks.compute_jld.s(pooled=False,
                                     path=bf,
                                     hash_prefix=cha,
                                     compute_params=compute_params,
                                     url_basename=url_basename,
                                     default=True))
        da.preanalysis_token = ta.id
        da.save()

    return res
