# Index of views for the fastSPT-GUI app
# A graphical user interface to the fastSPT tool by Anders S. Hansen, 2016
# By MW, GPLv3+, Feb.-Apr. 2017

##
## ==== Imports
##
import random, string, json, os, hashlib, pickle, urlparse, logging

from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .models import Analysis, Dataset
from django.http import HttpResponse
from django.template import loader

import celery, tasks, config

##
## ==== Global variables
##
hash_size = 16 ## Size of the prefix to save the fitted datasets
bf = "./static/analysis/" ## Location to save the fitted datasets


##
## === DBG VIEWS
##
if config.debug_views:
    logging.warning("'debug' is enabled")
    logging.warning("additional debug views have been loaded. Avoid that in production.")
    
    def barchart(request):
        """Returns a barchart template"""
        logging.warning("you called the `barchart` function, which is a 'debug' function, avoid that in production")
        template = loader.get_template('SPTGUI/barchart.html')
        context = {}
        return HttpResponse(template.render(context, request))

    def queue_status(request):
        """Returns the status of the queue"""
        logging.warning("you called the `queue_status` function, which is a 'debug' function, avoid that in production")        
        a = celery.app.control.inspect().reserved()['celery@alice']
        b = celery.app.control.inspect().active()['celery@alice']
        return HttpResponse(str(a)+str(b)+str(len(a))+" "+str(len(b)) )
    
    
##
## ==== Main views
##
def index(request):
    """Main view, returns the homepage template"""
    template = loader.get_template('SPTGUI/homepage.html')
    context = {'url_basename': get_unused_namepage()}
    return HttpResponse(template.render(context, request))

def analysis_root(request):
    """A simple placeholder text for the root of the analysis/ route"""
    return HttpResponse("There's nothing here...")

def analysis(request, url_basename):
    """Returns the analysis view. This is the main view of the system"""
    template = loader.get_template('SPTGUI/analysis.html')
    context = {'url_basename': url_basename}
    return HttpResponse(template.render(context, request))


## ==== Where are the views gone?
## view_import.py -> views providing statistics on the imported datasets
## views_tab_data.py -> Views involved in the display of the first tab (UploadController)

##
## ==== Other views
##


## ==== Analysis views
def analyze_api(request, url_basename):
    """This view, when called with a POST, starts the analysis (fitting of
    kinetic model) on a selection of datasets. When called with a GET, it 
    returns the progress of the analysis."""

    ana = get_object_or_404(Analysis, url_basename=url_basename)

    if request.method == 'GET': # return the '*_progress' object, if it exists
        cha = compute_hash(request.GET['hashvalue'])
        pa = bf+"{}/{}_progress.pkl".format(url_basename, cha)
        po = bf+"{}/{}_pooled.pkl".format(url_basename, cha)
        
        if os.path.exists(pa) :
            with open(pa, 'r') as f:
                save_pars = pickle.load(f)
            allgood = all([i['status']=='done' for i in save_pars['queue'].values()])
            return HttpResponse(json.dumps({'params': save_pars['pars'],
                                            'queue': save_pars['queue'],
                                            'allgood': allgood}),
                                content_type='application/json')
        else:
            return HttpResponse(json.dumps([pa+' not found']), content_type='application/json', status=400)

    elif request.method == 'POST': # Queue an analysis (but should be valid)
        fitparams = json.loads(request.body)
        cha = compute_hash(fitparams['hashvalue'])
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
            with open(prog_p, 'r') as f:
                save_pars = pickle.load(f)
            
            for data_id in fitparams['include'] : ## Difference in the queue dict
                if data_id not in save_pars['queue'] or save_pars['queue'][data_id]['status'] == 'error':
                    save_pars['queue'][data_id] = {'status': 'queued'}
                    to_process.append(data_id)
        if len(fitparams['include'])>1 and not 'pooled' in save_pars['queue']: ## To avoid recomputing
            save_pars['queue']['pooled'] = {'status': 'queued'} 
            
        ## Queue to celery
        with open(prog_p, 'w') as f: ## Write the fitting parameters to file
                pickle.dump(save_pars, f)
        for data_id in to_process:
            tasks.fit_jld.delay((bf, url_basename, cha, data_id))
        if len(fitparams['include'])>1 and save_pars['queue']['pooled']['status']=='queued':
            tasks.compute_jld.apply_async(kwargs={'dataset_id': None,
                                                  'pooled' : True,
                                                  'include':fitparams['include'],
                                                  'path': bf,
                                                  'hash_prefix': cha,
                                                  'url_basename': url_basename},
                                          link=tasks.fit_jld.s())
        return HttpResponse(json.dumps(''), content_type='application/json')
    
def get_analysis(request, url_basename, dataset_id, pooled=False):
    """Returns the fitted model of a given dataset, or a wait/error message.
    If `pooled==True`, the fitted pool is returned and the `dataset_id` argument
    is then ignored."""
    
    cha = compute_hash(request.GET['hashvalue'])    

    ## ==== Handle pooling
    if pooled:
        include = [int(i) for i in request.GET['include'].split(",")]
        if len(include)>1:
            pa = bf+"{}/{}_pooled.pkl".format(url_basename, cha)
        else: ## We are not really pooling, use existing data
            dataset_id = include[0]
            pa = bf+"{}/{}_{}.pkl".format(url_basename, cha, dataset_id)
            pooled = False
    else:
        pa = bf+"{}/{}_{}.pkl".format(url_basename, cha, dataset_id)

    ## ==== Actually generate the response
    if os.path.exists(pa):
        with open(pa, 'r') as f:
            save_pars = pickle.load(f)
            pa = save_pars['fit']
            fitparams = {}
            for k in save_pars['fitparams'].keys():
                fitparams[k] = save_pars['fitparams'][k].value
            return HttpResponse(json.dumps(
                {'fitparams': fitparams,
                 'fit': {'x': save_pars['fit']['x'].tolist(),
                         'y': save_pars['fit']['y'].tolist()}
             }), content_type='application/json')
    else:
        return HttpResponse(json.dumps('nothing ready here'), content_type='application/json', status=400) ## TODO MW /!\ not sure we should return 400...

def get_analysisp(request, url_basename):
    """Returns the fitted model for the currently selected datasets
    Note that it does not trigger the computation if no dataset has been 
    found."""
    return get_analysis(request, url_basename, None, pooled=True)

    
def get_jldp(request, url_basename):
    """Same as `get_jld` but returns the jld for the pooled values. In practice,
    the code is significantly different from the `get_jld` function since the 
    jump length distribution/histogram (jld) is stored in a pickled file. The
    name of this pickled file is generated based on the `include` parameters
    selected by the user. 
    Also, the jld is computed if it is not available."""
    
    if request.method == "GET":
        ## ==== Generate the path
        cha = compute_hash(request.GET['hashvalue'])    
        pa = bf+"{}/{}_pooled.pkl".format(url_basename, cha)

        save_params = {"status" : "notrun"}
        if os.path.exists(pa): ##  Probe for the computed histogram
            with open(pa, 'r') as f:
                save_params = pickle.load(f)
            if 'status' in save_params and save_params['status']=='done':
                jld = save_params['jld']
                return HttpResponse(json.dumps([jld[2].tolist(),
                                                jld[3].tolist()]),
                                    content_type='application/json')
 
        if save_params['status'] == 'notrun':
            save_params['status'] = 'queued'
            with open(pa, 'w') as f:
                pickle.dump(save_params, f)
            include = [int(i) for i in request.GET['include'].split(',')]
            logging.info("computing for values: {}".format(include))
            ## /!\ TODO MW Should check that the datasets belong to the
            ## right owner. Else one can download everybody's dataset...
            tasks.compute_jld.apply_async(
                kwargs={'dataset_id': None,
                        'pooled': True,
                        'include' : include,
                        'url_basename': url_basename,
                        'path' : bf,
                        'hash_prefix' : cha})
            
        return HttpResponse(json.dumps('computing'), content_type='application/json')
    
def get_jld(request, url_basename, dataset_id):
    """Returns the empirical jump length distribution (precomputed at the
    upload stage."""

    ## Sanity checks
    ana = get_object_or_404(Analysis, url_basename=url_basename)
    da = get_object_or_404(Dataset, analysis=ana, id=dataset_id)
     
    if check_jld(da): ## If the jld field is available in the database
        with open(da.jld.path, 'r') as f:
            jld = pickle.load(f)
        return HttpResponse(json.dumps([jld[2].tolist(), jld[3].tolist()]), content_type='application/json')
    else:
        return HttpResponse(json.dumps("JLD not ready"), content_type='application/json')
                 
    
## ==== Auxiliary functions
def check_jld(d):
    """Function to avoid an exception when checking whether a file exists 
    in the database"""
    try:
        return os.path.exists(d.jld.path)
    except:
        return False

def compute_hash(hashvalue):
    """Function that takes the 'hashvalue' of the GET request and compute a 
    reproducible hash from that"""
    cha = dict(urlparse.parse_qsl(
        urlparse.urlsplit("http://ex.org/?"+hashvalue).query))
    cha = hashlib.sha1(json.dumps(cha, sort_keys=True)).hexdigest()[:hash_size]
    return cha

def get_unused_namepage():
    """Function returns an unused, 10 chars identifier for an analysis"""
    N=10
    ret = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(N))
    while ret in [i.url_basename for i in Analysis.objects.all()]:
        ret = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(N))
    return ret
