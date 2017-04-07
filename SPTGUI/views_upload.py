# Index of views for the fastSPT-GUI app
# A graphical user interface to the fastSPT tool by Anders S. Hansen, 2016
# By MW, GPLv3+, Feb.-Apr. 2017
#
# Here we store views that relate to the upload of datasets

## ==== Imports
import os, json
import fileuploadutils2 as fuu
from django.http import HttpResponse
from flask import Response
from .models import Analysis, Dataset
from django.core.files import File
import celery, tasks
from django.utils import timezone

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
    re = HttpResponse()
    re.content = resp.data
    re.status_code = int(resp.status)

    if re.status_code == 200 and resp.ok:
        ## 1. Get the analysis object, or create it if it doesn't exist
        try:
            ana = Analysis.objects.get(url_basename=url_basename)
        except:
            ana = Analysis(url_basename=url_basename,
                           pub_date=timezone.now(),
                           name='',
                           description='')
            ana.save()
            os.makedirs("./static/analysis/"+url_basename) # Create folder for analyses


        ## 2. Create a database entry
        fi = File(open(json.loads(re.content)['address'], 'r')) ## This could be handled differently
        fi.name = json.loads(re.content)['filename']
        da = Dataset(analysis=ana,
                     name=request.POST['flowFilename'],
                     description='',
                     unique_id = json.loads(re.content)['unique_id'],
                     upload_status=True, # Upload is complete
                     preanalysis_status='uploaded', # Preanalysis not launched
                     data=fi)
        da.save()

        ## 3. Defer to the celery analysis
        ## Here we first perform the "check_input_file" task. If this one returns
        ## properly, the histogram of jump lengths distribution is computed
        ## (compute_jld).
        da.preanalysis_status='queued'
        ta = tasks.check_input_file.apply_async((da.data.path, da.id),
                                                link=tasks.compute_jld.s())
        da.preanalysis_token = ta.id
        da.save()

    return re
