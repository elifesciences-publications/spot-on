# Index of views for the fastSPT-GUI app
# A graphical user interface to the fastSPT tool by Anders S. Hansen, 2016
# By MW, GPLv3+, Feb.-Apr. 2017
#
# Here we store views that relate to the upload of datasets

## ==== Imports
import os, json, pickle
import fileuploadutils2 as fuu
from flask import Response

from .models import Analysis, Dataset
from django.core.files import File
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from celery import celery
import tasks


bf = "./static/analysis/" ## Location to save the fitted datasets


## ==== Views
def upload(request, url_basename):
    """A backend for the upload debugging stuff.
    /!\ We used to create the analysis in this view. This is no longer the case
    and now the creation is performed when the view is first displayed. This 
    should avoid issues with an analysis being created multiple times."""

    
    ## Call the original stuff
    ## Make sure we send the right stuff back.
    resp=Response()
    resp.ok = False
	
    filename=None
    responseTotalChunks=None
    """
    flow js always send a GET before a post, the first one give some information
    for the program to use to build the file when the upload is finished
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
        ana = get_object_or_404(Analysis, url_basename=url_basename)
        if not os.path.isdir(bf+url_basename):
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
                          'MaxJump' : 3,
                          'TimeGap' : 4.477}
        pick = {'params' : compute_params,
                'jld' : None,
                'status' : 'queued'}
        cha = 'c0f7e565600c3bf5'
        pa = bf+"{}/jld_{}_{}.pkl".format(url_basename, cha, da.id)
        with open(pa, 'w') as f: ## Save that we are computing
            pickle.dump(pick, f)
        
        da.preanalysis_status='queued'
        
        ta = celery.chain(tasks.check_input_file.s(da.data.path, da.id),
                          tasks.compute_jld.s(pooled=False,
                                              path=bf,
                                              hash_prefix=cha,
                                              compute_params=compute_params,
                                              url_basename=url_basename,
                                              default=True)).apply_async()
        #print ta.id, ta.parent.id 
        da.preanalysis_token = ta.id
        da.save()
        rr = json.loads(res.content)
        rr['celery_id'] = [ta.parent.id, ta.id]
        res.content = json.dumps(rr)
    return res
