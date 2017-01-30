from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from .models import Analysis, Dataset
from fileuploadutils import chunkOperationUtil

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

## ==== Views
def datasets_api(request, url_basename):
    """Function that exposes the list of available datasets, it is a view on the 
    Datasets library"""
    try:
        ana = Analysis.objects.get(name=url_basename)
    except:
        return HttpResponse(json.dumps([]), content_type='application/json')
    ret = [{'unique_id': d.unique_id,
            'filename' : d.filename, ## to check
            'title' :    d.title,
            'description' : d.description,
            'upload_status' : d.upload_status,
            'preanalysis_status' : d.preanalysis_status} for d in Dataset.objects.filter(name=ana)]
    return HttpResponse(json.dumps(ret), content_type='application/json')

@csrf_exempt
def upload(request, url_basename):
    context = {}
    resp = HttpResponse(json.dumps(context), content_type='application/json')

    filename=None
    responseTotalChunks=None
    """
    flow js always send a GET before a POST, the first
    one give some information for the program to use to
    build the file when the upload is finished
    """
    chunkOperationUtil(request,resp)

    ## Incorporate the upload to the database here
    ## 1. Handle the file reception
    ## 2. If the file is completed, save it to the database
    ## 3. Defer to the celery analysis
    
    return resp    

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
