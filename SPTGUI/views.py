from django.shortcuts import render
from django.utils import timezone
from .models import Analysis, Dataset
from fileuploadutils import chunkOperationUtil, checkValidityFile
from django.core.files import File

import celery, tasks

import random, string, json

# Create your views here.
from django.http import HttpResponse
from django.template import loader

def index(request):
    """Main view"""
    template = loader.get_template('SPTGUI/homepage.html')
    context = {'url_basename': get_unused_namepage()}
    return HttpResponse(template.render(context, request))

## ==== DEBUG
def upload_tmp(request):
    template = loader.get_template('SPTGUI/upload_tmp.html')
    return HttpResponse(template.render(request))

def queue_status(request):
    """Returns the status of the queue"""
    a = celery.app.control.inspect().reserved()['celery@alice']
    b = celery.app.control.inspect().active()['celery@alice']
    return HttpResponse(str(a)+str(b)+str(len(a))+" "+str(len(b)) )
def queue_new(request):
    """add stuff to the queue"""
    for i in range(20):
        celery.loong.delay()
    return HttpResponse("ok")



## ==== Views
def datasets_api(request, url_basename):
    """Function that exposes the list of available datasets, it is a view on the 
    Datasets library"""
    try:
        ana = Analysis.objects.get(url_basename=url_basename)
    except:
        return HttpResponse(json.dumps([]), content_type='application/json')
    ret = [{'id': d.id, ## the id of the Dataset in the database
            'unique_id': d.unique_id,
            'filename' : d.data.name,
            'name' :    d.name,
            'description' : d.description,
            'upload_status' : d.upload_status,
            'preanalysis_status' : d.preanalysis_status} for d in Dataset.objects.filter(analysis=ana)]
    return HttpResponse(json.dumps(ret), content_type='application/json')

def edit_api(request, url_basename):
    """Function to edit a dataset"""

    ## Filter the request
    if not request.method == 'POST':
        return HttpResponse(json.dumps(['error']), content_type='application/json')
    try:
        ana = Analysis.objects.get(url_basename=url_basename)
    except:
        return HttpResponse(json.dumps([]), content_type='application/json')
    try:
        body = json.loads(request.body)
        d = Dataset.objects.get(id=int(body['id']))
    except:
        return HttpResponse(json.dumps([]), content_type='application/json')

    ## Make the update
    d.name = body['dataset']['name']
    d.description = body['dataset']['description']
    d.save()

    ## Return something
    ret = {'id': d.id, ## the id of the Dataset in the database
            'unique_id': d.unique_id,
            'filename' : d.data.name,
            'name' :    d.name,
            'description' : d.description,
            'upload_status' : d.upload_status,
            'preanalysis_status' : d.preanalysis_status}
    return HttpResponse(json.dumps(ret), content_type='application/json')

def preprocessing_api(request, url_basename):
    """Function to poll the state of the preprocessing for all the datasets"""

    ## Filter the request
    if not request.method == 'GET':
        return HttpResponse(json.dumps(['error']), content_type='application/json')
    try:
        ana = Analysis.objects.get(url_basename=url_basename)
    except:
        return HttpResponse(json.dumps([]), content_type='application/json')

    ## Return result
    active = celery.app.control.inspect().active()['celery@alice']
    reserved = celery.app.control.inspect().reserved()['celery@alice']

    ## Make the junction by UUID
    
    ret_active = [{'uuid': d['id'],
                   'id' : Dataset.objects.get(preanalysis_token=d['id']).id,
                   'state': 'inprogress'} for d in active] ## /!\ to be Filtered by task type
    ret_scheduled = [{'uuid': d['id'],
                      'id' : Dataset.objects.get(preanalysis_token=d['id']).id,
                      'state': 'queued'} for d in reserved] ## /!\ to be Filtered by task
    ret = ret_active+ret_scheduled
    return HttpResponse(json.dumps(ret), content_type='application/json')    
    
def delete_api(request, url_basename):
    """Function to delete a dataset"""
    response = HttpResponse(json.dumps([]), content_type='application/json')
    response.status_code = 400
    if request.method == 'POST':
        ## Make all the checks that we need
        try: # Get the parameters
            body = json.loads(request.body)
        except:
            response.content = 'Cannot parse request'
            return response
        try: # Get the analysis
            ana = Analysis.objects.get(url_basename=url_basename)
        except:
            response.content = 'Analysis not found'
            return response
        try: # Get the dataset
            da = Dataset.objects.get(id=body['id'])
        except:
            response.content = 'Dataset not found'
            return response
        if body['filename'] != da.data.name:
            response.content = 'Dataset name not matching database'
            return response

        ## delete
        da.delete()
        response.status_code = 200
        return response
    
    return response

def upload(request, url_basename):
    context = {}
    response = HttpResponse(json.dumps(context), content_type='application/json')

    filename=None
    responseTotalChunks=None
    """
    flow js always send a GET before a POST, the first
    one give some information for the program to use to
    build the file when the upload is finished
    """
    if request.method == 'GET':
        (response.status_code, response.content) = checkValidityFile(request, response)
    elif request.method == 'POST':        
        (response.status_code, response.content) = chunkOperationUtil(request, response)
    if response.status_code == 200:
        ## 1. Get the analysis object, or create it if it doesn't exist
        try:
            ana = Analysis.objects.get(url_basename=url_basename)
        except:
            ana = Analysis(url_basename=url_basename,
                           pub_date=timezone.now(),
                           name='',
                           description='')
            ana.save()

        ## 2. Create a database entry
        fi = File(open(json.loads(response.content)['address'], 'r')) ## This could be handled differently
        fi.name = json.loads(response.content)['filename']
        da = Dataset(analysis=ana,
                     name=request.POST['flowFilename'],
                     description='',
                     unique_id = json.loads(response.content)['unique_id'],
                     upload_status=True, # Upload is complete
                     preanalysis_status='uploaded', # Preanalysis has not been launched
                     data=fi)
        da.save()

        ## 3. Defer to the celery analysis
        da.preanalysis_status='queued'
        ta = tasks.check_input_file.delay(da.data.path, da.id)
        da.preanalysis_token = ta.id
        da.save()

    return response

def analysis_root(request):
    return HttpResponse("There's nothing here...")

def analysis(request, url_basename):
    """Returns the analysis view"""
    template = loader.get_template('SPTGUI/analysis.html')
    context = {'url_basename': url_basename}
    return HttpResponse(template.render(context, request))

## ==== Auxiliary functions
def get_unused_namepage():
    """Function returns an unused, 10 chars identifier for an analysis"""
    N=10
    ret = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(N))
    while ret in [i.url_basename for i in Analysis.objects.all()]:
        ret = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(N))
    return ret
