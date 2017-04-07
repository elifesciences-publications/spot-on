# Index of views for the fastSPT-GUI app
# A graphical user interface to the fastSPT tool by Anders S. Hansen, 2016
# By MW, GPLv3+, Feb.-Apr. 2017
#
# Here we store views that are routes for the first tab (corresponding to the
# uploadController in Angular.

## ==== Imports
import json, os, celery, logging
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from .models import Analysis, Dataset

## ==== Views
def statistics(request, url_basename):
    """Function returns some global statistics about all the datasets"""
    ana = get_object_or_404(Analysis, url_basename=url_basename)
    try:
        da = Dataset.objects.filter(analysis=ana, preanalysis_status='ok')
    except:
        return HttpResponse(json.dumps({'status': 'error',
                                        'message': 'dataset not found'}),
                            content_type='application/json', status=400)
    if len(da)==0:
        return HttpResponse(
            json.dumps({'status': 'error',
                        'message': 'no properly uploaded dataset'}),
            content_type='application/json', status=400)
    res = {'status' : 'ok',
           'ok_traces' : len(da),
           'ntraces' : sum([i.pre_ntraces for i in da]),
           'npoints' : sum([i.pre_npoints for i in da]),
       }
                            
    return HttpResponse(json.dumps(res), content_type='application/json')    

def datasets_api(request, url_basename):
    """
    Function that exposes the list of available datasets for a given analysis 
    (that is, a given url, specified by the `url_basename` (str) parameter, it is
    a view on the Datasets library
    """
    
    def check_jld(d):
        """Small helper function to check if we have a JLD stored"""
        try:
            return os.path.exists(d.jld.path)
        except:
            return False
        
    ana = get_object_or_404(Analysis, url_basename=url_basename)
    ret = [{'id': d.id, ## the id of the Dataset in the database
            'unique_id': d.unique_id,
            'filename' : d.data.name,
            'name' :    d.name,
            'description' : d.description,
            'upload_status' : d.upload_status,
            'preanalysis_status' : d.preanalysis_status,
            'pre_ntraces' : d.pre_ntraces,
            'pre_npoints' : d.pre_npoints,
            'jld_available': check_jld(d),
        } for d in Dataset.objects.filter(analysis=ana)]
    
    return HttpResponse(json.dumps(ret), content_type='application/json')

def edit_api(request, url_basename):
    """Function to edit a dataset

    So far the following fields of the database are handled:
    - name
    - description
    """

    ## Filter the request
    if not request.method == 'POST':
        return HttpResponse(json.dumps(['error']), content_type='application/json')
    
    ana = get_object_or_404(Analysis, url_basename=url_basename)

    try:
        body = json.loads(request.body)
        d = get_object_or_404(Dataset, id=int(body['id']))
    except:
        logging.error("In function `edit_api`, the `id` field was not found in the POST body, body content: {}".format(body))
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
    """Function to poll the state of the preprocessing for all the datasets.
    Preprocessing mostly consists of the asynchronous task `check_input_file`."""

    ## Filter the request
    if not request.method == 'GET':
        return HttpResponse(json.dumps(['error']), content_type='application/json')

    ana = get_object_or_404(Analysis, url_basename=url_basename)

    active = []
    reserved = []
    for i in celery.app.control.inspect().active().values():
        active += i#celery.app.control.inspect().active()['celery@alice']
    for i in celery.app.control.inspect().reserved().values():
        reserved += i#celery.app.control.inspect().reserved()#['celery@alice']
    active = [i for i in active if i['name'] == 'SPTGUI.tasks.check_input_file']
    reserved = [i for i in reserved if i['name'] == 'SPTGUI.tasks.check_input_file']

    ## Make the junction by UUID
    ret_active = [{'uuid': d['id'],
                   'id' : Dataset.objects.get(preanalysis_token=d['id']).id,
                   'state': 'inprogress'} for d in active]
    ret_scheduled = [{'uuid': d['id'],
                      'id' : Dataset.objects.get(preanalysis_token=d['id']).id,
                      'state': 'queued'} for d in reserved]
    ret = ret_active+ret_scheduled
    return HttpResponse(json.dumps(ret), content_type='application/json')    
    
def delete_api(request, url_basename):
    """Function to delete a dataset"""
    response = HttpResponse(json.dumps([]),
                            content_type='application/json',
                            status=400)
    
    if request.method == 'POST':
        ## Make all the checks that we need
        try: # Get the parameters
            body = json.loads(request.body)
        except:
            response.content = 'Cannot parse request'
            return response
        ana = get_object_or_404(Analysis, url_basename=url_basename) # Get the analysis
        da = get_object_or_404(Dataset, id=int(body['id']))

        if body['filename'] != da.data.name:
            response.content = 'Dataset name not matching database'
            return response

        da.delete()         ## delete
        response.status_code = 200
        return response
    
    return response
