from django.shortcuts import render
from django.utils import timezone
from .models import Analysis, Dataset
#from fileuploadutils import chunkOperationUtil, checkValidityFile
import fileuploadutils2 as fuu
from django.core.files import File
from flask import Response
import celery, tasks
from django.views.decorators.csrf import csrf_exempt
from wsgiref.util import FileWrapper

import random, string, json, os, hashlib, pickle, urlparse

from django.http import HttpResponse
from django.template import loader

def index(request):
    """Main view"""
    template = loader.get_template('SPTGUI/homepage.html')
    context = {'url_basename': get_unused_namepage()}
    return HttpResponse(template.render(context, request))
    
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

def barchart(request):
    """Returns a barchart template"""
    template = loader.get_template('SPTGUI/barchart.html')
    context = {}
    return HttpResponse(template.render(context, request))
    


## ==== Views
def statistics(request, url_basename):
    """Function returns some global statistics about all the datasets"""
    ## Sanity checks
    try:
        ana = Analysis.objects.get(url_basename=url_basename)
    except:
        return HttpResponse(json.dumps({'status': 'error',
                                        'message': 'analysis not found'}),
                            content_type='application/json')
    try:
        da = Dataset.objects.filter(analysis=ana, preanalysis_status='ok')
    except:
        return HttpResponse(json.dumps({'status': 'error',
                                        'message': 'dataset not found'}),
                            content_type='application/json')
    if len(da)==0:
        return HttpResponse(json.dumps({'status': 'error',
                                        'message': 'no properly uploaded dataset'}),
                            content_type='application/json')
    res = {'status' : 'ok',
           'ok_traces' : len(da),
           'ntraces' : sum([i.pre_ntraces for i in da]),
           'npoints' : sum([i.pre_npoints for i in da]),
       }
                            
    return HttpResponse(json.dumps(res), content_type='application/json')

def dataset_original(request, url_basename, dataset_id):
    """Function that return a pointer to the original file"""

    ## Sanity checks
    try:
        ana = Analysis.objects.get(url_basename=url_basename)
    except:
        return HttpResponse(json.dumps(['analysis not found']),
                            content_type='application/json')
    try:
        da = Dataset.objects.get(analysis=ana, id=dataset_id)
    except:
        return HttpResponse(json.dumps(['dataset not found']),
                            content_type='application/json')

    ## Return data
    response = HttpResponse(FileWrapper(da.data.file), content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename={}'.format(os.path.basename(da.data.path))
    return response
        

def dataset_parsed(request, url_basename, dataset_id):
    """Function that return a pointer to the parsed file"""
    try:
        ana = Analysis.objects.get(url_basename=url_basename)
    except:
        return HttpResponse(json.dumps(['analysis not found']),
                            content_type='application/json')
    try:
        da = Dataset.objects.get(analysis=ana, id=dataset_id)
    except:
        return HttpResponse(json.dumps(['dataset not found']),
                            content_type='application/json')

    ## Return data
    response = HttpResponse(FileWrapper(da.parsed.file), content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename={}'.format(os.path.basename(da.parsed.path))
    return response

def dataset_report(request, url_basename, dataset_id):
    """Function that return a pointer to the importation report"""
    try:
        ana = Analysis.objects.get(url_basename=url_basename)
    except:
        return HttpResponse(json.dumps(['analysis not found']),
                            content_type='application/json')
    try:
        da = Dataset.objects.get(analysis=ana, id=dataset_id)
    except:
        return HttpResponse(json.dumps(['dataset not found']),
                            content_type='application/json')

    ## Return data
    response = HttpResponse(json.dumps(['this is a useless report']),
                            content_type='application/json')
    return response
    

def datasets_api(request, url_basename):
    """Function that exposes the list of available datasets, it is a view on the 
    Datasets library"""
    def check_jld(d):
        try:
            return os.path.exists(d.jld.path)
        except:
            return False
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
            'preanalysis_status' : d.preanalysis_status,
            'pre_ntraces' : d.pre_ntraces,
            'pre_npoints' : d.pre_npoints,
            'jld_available': check_jld(d),
        } for d in Dataset.objects.filter(analysis=ana)]
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

    print celery.app.control.inspect().active()
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

        da.delete()         ## delete
        response.status_code = 200
        return response
    
    return response

## ==== Analysis
def analyze_api(request, url_basename):
    """This view, when called with a POST, starts the analysis (fitting of
    kinetic model) on a selection of datasets. When called with a GET, it 
    returns the progress of the analysis."""
    hash_size = 16
    bf = "./static/analysis/"

    try:
        ana = Analysis.objects.get(url_basename=url_basename)
    except:
        return HttpResponse(json.dumps(['analysis not found or no data uploaded']), content_type='application/json')

    if request.method == 'GET': # return the '*_progress' object, if it exists
        cha = dict(urlparse.parse_qsl(
            urlparse.urlsplit("http://ex.org/?"+request.GET['hashvalue']).query))
        cha = hashlib.sha1(json.dumps(cha, sort_keys=True)).hexdigest()[:hash_size]
        pa = bf+"{}/{}_progress.pkl".format(url_basename, cha)
        if os.path.exists(pa) :
            with open(pa, 'r') as f:
                save_pars = pickle.load(f)
            allgood = all([i['status']=='done' for i in save_pars['queue'].values()])
            return HttpResponse(json.dumps({'params': save_pars['pars'],
                                            'queue': save_pars['queue'],
                                            'allgood': allgood}),
                                content_type='application/json')
        else:
            # TODO MW: say that we are sad (say it with an error code)
            return HttpResponse(json.dumps([pa+' not found']), content_type='application/json')

    elif request.method == 'POST': # Queue an analysis (but should be valid)
        fitparams = json.loads(request.body)
        cha = dict(urlparse.parse_qsl(
            urlparse.urlsplit("http://ex.org/?"+fitparams['hashvalue']).query))
        cha = hashlib.sha1(json.dumps(cha, sort_keys=True)).hexdigest()[:hash_size]

        prog_p = bf+"{}/{}_progress.pkl".format(url_basename, cha)
        to_process = []
        if not os.path.exists(prog_p): ## Create the pickle file
            
            save_pars = {'pars': fitparams,
                         'queue': {},
                         'fit': {},
                         'date_created': timezone.now(),
                         'date_modified': timezone.now()}
            
            with open(prog_p, 'w') as f: ## Write the fitting parameters to file
                pickle.dump(save_pars, f)
                
            ## Queue to Celery: loop over the datasets
            for data_id in fitparams['include']:
                save_pars['queue'][data_id] = {'status': 'queued'}
                to_process.append(data_id)
                
        else: ## Determine the new stuff to be run
            with open(prog_p, 'r') as f: ## Load the pickle file
                save_pars = pickle.load(f)
            
            for data_id in fitparams['include'] : ## Difference in the queue dict
                if data_id not in save_pars['queue'] or save_pars['queue'][data_id]['status'] == 'error':
                    save_pars['queue'][data_id] = {'status': 'queued'}
                    to_process.append(data_id)
            
        ## Queue to celery
        with open(prog_p, 'w') as f: ## Write the fitting parameters to file
                pickle.dump(save_pars, f)
        for data_id in to_process:
            tasks.fit_jld.delay(bf, url_basename, cha, data_id)

        return HttpResponse(json.dumps(cha), content_type='application/json') # DBG

def get_analysis(request, url_basename, dataset_id):
    """Returns the fitted model of a given dataset, or a wait/error message."""
    hash_size=16
    bf = "./static/analysis/"
    
    cha = dict(urlparse.parse_qsl(
        urlparse.urlsplit("http://ex.org/?"+request.GET['hashvalue']).query))
    cha = hashlib.sha1(json.dumps(cha, sort_keys=True)).hexdigest()[:hash_size]
    pa = bf+"{}/{}_{}.pkl".format(url_basename, cha, dataset_id)
    if os.path.exists(pa) :
        with open(pa, 'r') as f:
            save_pars = pickle.load(f)
            pa = save_pars['fit']
            return HttpResponse(json.dumps([pa[2].tolist(), pa[3].tolist()]), content_type='application/json')
    else:
        return HttpResponse(json.dumps('nothing ready here'), content_type='application/json')


                 
#### ==== UPLOAD STUFF    
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
                     preanalysis_status='uploaded', # Preanalysis has not been launched
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
