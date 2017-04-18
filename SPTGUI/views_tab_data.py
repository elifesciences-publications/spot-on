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
import SPTGUI.statistics as stats

## ==== Views
# def statistics(request, url_basename):
#     """Function returns some global statistics about all the datasets"""
#     logging.warning('This function (views_tab_data.statistics) is deprecated')
    
#     def mean(m,e):
#         """Compute a weighted mean, given a list of individual means (m)
#         and a list of 'effectifs'"""
#         return sum([i*j for (i,j) in zip(m,e)])/sum(e)

#     try:
#         ana = get_object_or_404(Analysis, url_basename=url_basename)
#     except:
#         return HttpResponse(json.dumps({'status': 'error',
#                                         'message': 'analysis does not exist'}),
#                             content_type='application/json')
#     try:
#         da = Dataset.objects.filter(analysis=ana, preanalysis_status='ok')
#     except:
#         return HttpResponse(json.dumps({'status': 'error',
#                                         'message': 'dataset not found'}),
#                             content_type='application/json', status=400)
#     if len(da)==0:
#         return HttpResponse(
#             json.dumps({'status': 'empty',
#                         'message': 'no properly uploaded dataset'}),
#             content_type='application/json')

#     comp_ltraj = stats.global_mean_median(da, stats.length_of_trajectories)
#     comp_ppf = stats.global_mean_median(da, stats.particles_per_frame, reindex_frames=True)
#     comp_jlength = stats.global_mean_median(da, stats.jump_length)
    
#     res = {'status' : 'ok',
#            'ok_traces' : len(da),
#            'pre_ntraces' : sum([i.pre_ntraces for i in da]),
#            'pre_npoints' : sum([i.pre_npoints for i in da]),
#            'pre_ntraces3': sum([i.pre_ntraces3 for i in da]),
#            'pre_nframes' : sum([i.pre_nframes for i in da]),
#            'pre_njumps'  : sum([i.pre_njumps for i in da]),
#            'pre_median_length_of_trajectories' : comp_ltraj['median'],
#            'pre_mean_length_of_trajectories' : comp_ltraj['mean'],
#            'pre_median_particles_per_frame' : comp_ppf['median'],
#            'pre_mean_particles_per_frame' : comp_ppf['mean'],
#            'pre_median_jump_length' : comp_jlength['median'],
#            'pre_mean_jump_length' : comp_jlength['median'],
#        }
                            
#     return HttpResponse(json.dumps(res), content_type='application/json')    

def datasets_api(request, url_basename):
    """
    Function that exposes the list of available datasets for a given analysis 
    (that is, a given url, specified by the `url_basename` (str) parameter, it is
    a view on the Datasets library
    """

    logging.warning('This function (views_tab_data.datasets_api) is deprecated')
    
    try:
        ana = get_object_or_404(Analysis, url_basename=url_basename)
    except:
        return HttpResponse(json.dumps([]),
                            content_type='application/json')
    
    ret = [{'id': d.id, ## the id of the Dataset in the database
            'unique_id': d.unique_id,
            'filename' : d.data.name,
            'name' :    d.name,
            'description' : d.description,
            'upload_status' : d.upload_status,
            'preanalysis_status' : d.preanalysis_status,

            ## Preanalysis statistics
            'pre_ntraces' : d.pre_ntraces,
            'pre_npoints' : d.pre_npoints,
            'pre_ntraces3' : d.pre_ntraces3,
            'pre_nframes' : d.pre_nframes,
            'pre_njumps' : d.pre_njumps,
            'pre_median_length_of_trajectories' : d.pre_median_length_of_trajectories,
            'pre_mean_length_of_trajectories' : d.pre_mean_length_of_trajectories,
            'pre_median_particles_per_frame' : d.pre_median_particles_per_frame,
            'pre_mean_particles_per_frame' : d.pre_mean_particles_per_frame,
            'pre_median_jump_length' : d.pre_median_jump_length,
            'pre_mean_jump_length' : d.pre_mean_jump_length,
            
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

    print "This 'preprocessing_api' is deprecated. Don't use it"
    ## Filter the request
    if not request.method == 'GET':
        return HttpResponse(json.dumps(['error']), content_type='application/json')

    ana = get_object_or_404(Analysis, url_basename=url_basename)

    ltasks  = ['SPTGUI.tasks.check_input_file']#, 'SPTGUI.tasks.compute_jld']
    active = []
    reserved = []
    act_obj = celery.app.control.inspect().active()
    if act_obj != None:
        for i in act_obj.values():
            active += i
            
    res_obj = celery.app.control.inspect().reserved()
    if res_obj != None:
        for i in res_obj.values():
            reserved += i
    active = [i for i in active if i['name'] in ltasks]
    reserved = [i for i in reserved if i['name'] in ltasks]

    ## Make the junction by UUID
    ana = Analysis.objects.get(url_basename=url_basename)
    run = Dataset.objects.filter(analysis=ana)
    ret = []
    
    for d in run:
        if d.preanalysis_token == '': ## Check if the jld has been computed
            if not check_jld(d): 
                ret.append({'uuid': d.preanalysis_token,
                            'id' : d.id,
                            'state': 'computing jld'})
            else:
                ret.append({'uuid': d.preanalysis_token,
                            'id' : d.id,
                            'state': 'ok'})
        elif d.preanalysis_token in [i['id'] for i in active]:
            ret.append({'uuid': d.preanalysis_token,
                   'id' : d.id,
                   'state': 'inprogress'})
        elif d.preanalysis_token in [i['id'] for i in reserved]:
            ret.append({'uuid': d.preanalysis_token,
                   'id' : d.id,
                   'state': 'queued'})
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

## ==== Helper functions
def check_jld(d):
    """Small helper function to check if we have a JLD stored"""
    try:
        return os.path.exists(d.jld.path)
    except:
        return False
