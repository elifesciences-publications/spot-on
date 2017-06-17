# Index of views for the fastSPT-GUI app
# A graphical user interface to the fastSPT tool by Anders S. Hansen, 2016
# By MW, GPLv3+, Feb.-Apr. 2017

##
## ==== Imports
##
import random, string, json, os, hashlib, pickle, urlparse, logging, re
from haikunator import Haikunator
import fastspt

from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.db import transaction
from .models import Analysis, Dataset
from django.http import HttpResponse
from django.template import loader
from django.conf import settings
import fastSPT.custom_settings as custom_settings

from celery import celery
import tasks, config, recaptcha
import fitted_zcor

# ==== Initialization
# careful a similar code exists in sockets_kinetics.py
paths = {0: "./SPTGUI/fit_zcorr/0gaps",
         1: "./SPTGUI/fit_zcorr/1gaps",
         2: "./SPTGUI/fit_zcorr/2gaps"}
tree_init = fitted_zcor.init(paths=paths)
haikunator = Haikunator()
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

    def popover(request):
        """Returns a simple popover, inspired from:
        http://plnkr.co/edit/ccb5MR?p=preview"""
        logging.warning("you called the `popover` function, which is a 'debug' function, avoid that in production")
        template = loader.get_template('SPTGUI/popover.html')
        context = {}
        return HttpResponse(template.render(context, request))            
    
##
## ==== Main views
##
def analysis_root(request):
    """A simple placeholder text for the root of the analysis/ route"""
    return HttpResponse("There's nothing here...")

def new_analysis(request):
    """The view that create a new analysis. This is the only way to create 
    a new analysis."""
    if request.method == "POST" or not custom_settings.RECAPTCHA_USE:
        ## Validate CAPTCHA
        if custom_settings.RECAPTCHA_USE:
            ip = recaptcha.get_client_ip(request)
            captcha_ok = recaptcha.grecaptcha_verify(request, custom_settings.RECAPTCHA_SECRET)

            if not captcha_ok['message']:
                return HttpResponse("Failed CAPTCHA, reason {}".format(captcha_ok['message']))
        
        ## Generate a name
        url_basename = get_unused_namepage()
        
        ## Create the analysis if needed
        ana = Analysis(url_basename=url_basename,
                       pub_date=timezone.now(),
                       name='',
                       description='')
        ana.save()
        return redirect('SPTGUI:analysis', url_basename)
    else:
        return redirect('SPTGUI:index')

def new_demo(request):
    """Function that initiates a new demo analysis (with default datasets)"""
    if request.method == "POST" or not custom_settings.RECAPTCHA_USE:
        ## Validate CAPTCHA
        if custom_settings.RECAPTCHA_USE:
            ip = recaptcha.get_client_ip(request)
            captcha_ok = recaptcha.grecaptcha_verify(request, custom_settings.RECAPTCHA_SECRET)

            if not captcha_ok['message']:
                return HttpResponse("Failed CAPTCHA, reason {}".format(captcha_ok['message']))
        
        ## Generate a name
        url_basename = get_unused_namepage()
        
        ## Duplicate the related datasets
        dem = Analysis.objects.get(id=custom_settings.demo_id)
        da = Dataset.objects.filter(analysis=dem)        
        print "The original analysis is {} and has {} datasets".format(dem.url_basename, len(da))
        
        ## Duplicate a demo analysis
        dem.id = None
        dem.pk = None
        dem.url_basename = url_basename
        dem.editable = True
        dem.pub_date=timezone.now()
        dem.save()

        for d in da:
            d.pk = None
            d.id = None
            d.analysis = dem
            d.save()

        ## Create the storage folder
        os.makedirs(os.path.join(bf,url_basename))

        print "New id: ", dem.id, " new name: ", url_basename
        return redirect('SPTGUI:analysis', url_basename)
    else:
        return redirect('../..')
    
    
def index(request):
    """Main view, returns the homepage template"""
    template = loader.get_template('SPTGUI/homepage.html')
    context = {'url_basename': 'new',
               'active': 'home',
               'captcha': custom_settings.RECAPTCHA_USE,
               'recaptchakey': custom_settings.RECAPTCHA_PUBLIC}
    return HttpResponse(template.render(context, request))

def analysis(request, url_basename, run_tests=False):
    """Returns the analysis view. This is the main view of the system"""
    ana = get_object_or_404(Analysis, url_basename=url_basename)
    if not ana.editable:
        return HttpResponse('You cannot access this page') # Quick'n'dirty
    ana.acc_date = timezone.now()
    template = loader.get_template('SPTGUI/analysis.html')
    context = {'url_basename': url_basename,
               'active': 'analysis',
               'run_tests': run_tests,
               'lightlogo': True,
               'version': settings.APP_VERSION,
               'versionbackend': fastspt.__version__}
    ana.save()
    return HttpResponse(template.render(context, request))

def analysis_dbg(request, url_basename):
    if config.debug_views:
        print "Executing debug view"
        return analysis(request, url_basename, run_tests=True)

def static(request, page):
    """Returns a static page"""
    doc_versions = [0.6, 0.7]
    templates = {"docs": "documentation.html",
                 "about": "about.html",
                 "contact": "contact.html",
                 "license": "license.html",
                 "about": "about.html"}
    context = {}
    templates_docs = {"docs/{}".format(k): "{}/{}".format(k, templates["docs"]) for k in doc_versions}
    for k in templates_docs:
        templates[k] = templates_docs[k]
    if config.debug_views:
        templates["docs_viz"] = "docs_viz.html"
    if page == 'docs':
        return redirect('SPTGUI:staticpage', 'docs/latest')
    elif page.startswith('docs/'):
        version = page.split('/')[1]
        context["versions"] = [{"version": i,
                                "url": "docs/{}".format(i)} for i in doc_versions]
        context["latest_version"] = False
        context["latest_version_number"] = str(doc_versions[-1])
        context["version_number"] = version
        
        if version not in [str(i) for i in doc_versions]: 
            version = 'latest'
        print "-- version", version, str(doc_versions[-1]), version == str(doc_versions[-1])
        if version == 'latest' or version == str(doc_versions[-1]):
            page = "docs/{}".format(doc_versions[-1])
            context["latest_version"] = True
            context["version_number"] = str(doc_versions[-1])
            
    if page in templates:                
        template = loader.get_template('SPTGUI/{}'.format(templates[page]))
        context["active"] = page
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
        cha = compute_hash2(request.GET['hashvalue'], request.GET['hashvalueJLD'])
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
        ids = []
        noids = []
        compute_pool = False
        
        (jldparams, fitparams) = json.loads(request.body)
        fitparams['ModelFit'] = [1,2][fitparams['ModelFit']]
        fitparams['fit2states'] = {'false': False, 'true': True}[fitparams["fit2states"]]

        ## Get the corrected z_cor parameters
        zcor = fitted_zcor.query_nearest(fitparams['dTfit'],
                                         fitparams['dZfit'],
                                         jldparams['GapsAllowed'],
                                         tree_init)
        fitparams["a"] = zcor["params"][0]
        fitparams["b"] = zcor["params"][1]
        
        ## Clean the params object
        scf = fitparams['SingleCellFit']
        fitparams.pop('SingleCellFit')
        fitparams.pop('dZfit')
        fitparams.pop('dTfit')
        
        cha_jld = compute_hash(jldparams['hashvalueJLD'])
        cha_fit = compute_hash(fitparams['hashvalue'])
        cha = cha_fit+cha_jld
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
            if scf or len(fitparams['include'])==1:
                for data_id in fitparams['include']:
                    save_pars['queue'][data_id] = {'status': 'queued'}
                    to_process.append(data_id)
                
        else: ## Determine the new stuff to be run
            with open(prog_p, 'r') as f:
                save_pars = pickle.load(f)
            if scf or len(fitparams['include'])==1:
                for data_id in fitparams['include'] : ## Difference in the queue dict
                    if data_id not in save_pars['queue'] or save_pars['queue'][data_id]['status'] == 'error':
                        save_pars['queue'][data_id] = {'status': 'queued'}
                        to_process.append(data_id)
                    else:
                        noids.append({'celery_id': 'none', 'database_id': data_id})
        if len(fitparams['include'])>1 and not 'pooled' in save_pars['queue']: ## To avoid recomputing
            save_pars['queue']['pooled'] = {'status': 'queued'} 
            
        ## Queue to celery
        with open(prog_p, 'w') as f: ## Write the fitting parameters to file
                pickle.dump(save_pars, f)

        for data_id in to_process:
            ta = tasks.fit_jld.delay((bf, url_basename, cha_jld, data_id), cha_fit)
            ids.append({'celery_id': ta.id, 'database_id': data_id})
        if len(fitparams['include'])>1 and save_pars['queue']['pooled']['status']=='queued':
            jldparams.pop('hashvalueJLD')
            ta = celery.chain(tasks.compute_jld.s(dataset_id=None,
                                                  pooled=True,
                                                  include=fitparams['include'],
                                                  path=bf,
                                                  hash_prefix=cha_jld,
                                                  compute_params=jldparams,
                                                  url_basename=url_basename),
                              tasks.fit_jld.s(cha_fit)).apply_async()
                                                          
            ids.append({'celery_id': ta.id, 'database_id': 'pooled'})
            compute_pool = True

        if not compute_pool:
            noids.append({'celery_id': 'none', 'database_id': 'pooled'})
        print "returning", ids, noids

        return HttpResponse(json.dumps(ids+noids), content_type='application/json')
    
def get_analysis(request, url_basename, dataset_id, pooled=False):
    """Returns the fitted model of a given dataset, or a wait/error message.
    If `pooled==True`, the fitted pool is returned and the `dataset_id` argument
    is then ignored."""
    
    cha = compute_hash2(request.GET['hashvalue'], request.GET['hashvalueJLD'])    

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
            fitparams = {'l2': save_pars['fit_ssq2'],
                         'aic': save_pars['fit_aic'],
                         'bic': save_pars['fit_bic']}
            for k in save_pars['fitparams'].keys():
                fitparams[k] = float(save_pars['fitparams'][k].value)
                fitparams[k+"_std"] = float(save_pars['fitparams'][k].stderr)
            fitparams["fit2states"] = save_pars['params']["fit2states"]
            fitparams["fitSigma"] = save_pars['params']["fitSigma"]
            
            if not fitparams["fit2states"]:
                if fitparams["D_med"]>fitparams["D_fast"]:
                    tmp = fitparams["D_med"]#.copy()
                    tmp_std = fitparams["D_med_std"]#.copy()
                    fitparams["D_med"] = fitparams["D_fast"]#.copy()
                    fitparams["D_med_std"] = fitparams["D_fast_std"]#.copy()
                    fitparams["D_fast"] =tmp
                    fitparams["D_fast_std"] = tmp_std
            print fitparams
            return HttpResponse(json.dumps(
                {'status': 'done',
                 'fitparams': fitparams,
                 'fit': {'x': save_pars['fit']['x'].tolist(),
                         'y': save_pars['fit']['y'].tolist()}
             }), content_type='application/json')
    else:
        return HttpResponse(json.dumps({'status': 'notready'}), content_type='application/json')

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

    ## Sanity checks
    ana = get_object_or_404(Analysis, url_basename=url_basename)    
    
    if request.method == "GET":
        ## ==== Generate the path
        fitparams = request.GET
        cha = compute_hash(fitparams['hashvalueJLD'])
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
            save_params['params'] = fitparams
            with open(pa, 'w') as f:
                pickle.dump(save_params, f)
            include = [int(i) for i in request.GET['include'].split(',')]
            logging.info("computing for values: {}".format(include))
            ## /!\ TODO MW Should check that the datasets belong to the
            ## right owner. Else one can download everybody's dataset...
            logging.warning("Should check that the datasets belong to the right owner. Else one can download everybody's dataset...")
            keys = ["BinWidth", "GapsAllowed", "TimePoints", "JumpsToConsider", "MaxJump", "TimeGap", "useAllTraj"]
            keytip = [float, int, int, int, float, float]
            compute_params = {k: t(float(fitparams[k])) for (k,t) in zip(keys,keytip)}
            tasks.compute_jld.apply_async(
                kwargs={'dataset_id': None,
                        'pooled': True,
                        'include' : include,
                        'url_basename': url_basename,
                        'compute_params': compute_params,
                        'path' : bf,
                        'hash_prefix' : cha})
            
        return HttpResponse(json.dumps('computing'), content_type='application/json')


def get_jld_default(request, url_basename, dataset_id):
    """Returns the empirical jump length distribution (precomputed at the
    upload stage. That is, the default jump length distribution."""

    ## Sanity checks
    ana = get_object_or_404(Analysis, url_basename=url_basename)
    da = get_object_or_404(Dataset, analysis=ana, id=dataset_id)
     
    if check_jld(da): ## If the jld field is available in the database
        with open(da.jld.path, 'r') as f:
            jld = pickle.load(f)
        return HttpResponse(
            json.dumps({'status': 'done',
                        'jld': [jld[2].tolist(), jld[3].tolist()]}),
                       content_type='application/json')
    else:
        return HttpResponse(json.dumps("JLD not ready"), content_type='application/json')

def get_jld(request, url_basename):
    """Returns the empirical jump length distribution based on a custom set of 
    parameters. This does the job for all the uploaded datasets."""

    ## Sanity checks
    try: 
        ana = get_object_or_404(Analysis, url_basename=url_basename)
    except:
        return HttpResponse(json.dumps([]),
                            content_type='application/json')
    
    dataset_ids = [d.id for d in Dataset.objects.filter(analysis=ana)]

    ## Compute the distribution if we have a POST
    if request.method == "POST":
        task_ids = []
        for dataset_id in dataset_ids:
            fitparams = json.loads(request.body)
            cha = compute_hash(fitparams['hashvalueJLD'])
            bn = bf+url_basename
            pa = bf+"{}/jld_{}_{}.pkl".format(url_basename, cha, dataset_id)

            if not os.path.exists(pa):
                compute = True
                pick = {'params' : fitparams,
                        'jld' : None,
                        'status' : 'queued'}
            else:
                with open(pa, 'r') as f:
                    pick = pickle.load(f)
                if 'status' in pick and pick['status'] not in ('queued', 'done'):
                    compute = True
                    pick['status'] = 'queued'
                else:
                    compute = False

            ## Get ready to run the task
            if compute:
                if not os.path.isdir(bn):
                    logging.info("Creating directory for analysis: {}".format(url_basename))
                    os.mkdir(bn)
                with open(pa, 'w') as f: ## Save that we are computing
                    pickle.dump(pick, f)
                keys = ["BinWidth", "GapsAllowed", "TimePoints", "JumpsToConsider", "MaxJump", "TimeGap", "useAllTraj"]
                compute_params = {k: fitparams[k] for k in keys}
                ta = tasks.compute_jld.apply_async(
                    kwargs={'dataset_id': dataset_id,
                            'pooled' : False,
                            'path': bf,
                            'hash_prefix': cha,
                            'compute_params': compute_params,
                            'url_basename': url_basename})
                task_ids.append({'celery_id': ta.id, 'database_id': dataset_id})
        return HttpResponse(json.dumps(task_ids), content_type='application/json')
    
    elif request.method == 'GET': ## Return what we have if this is a GET
        ready = True
        ret = []
        for dataset_id in dataset_ids:
            cha = compute_hash(request.GET['hashvalueJLD'])    
            pa = bf+"{}/jld_{}_{}.pkl".format(url_basename, cha, dataset_id)

            if os.path.exists(pa):
                with open(pa, 'r') as f:
                    pick = pickle.load(f)
                    if 'status' in pick and pick['status']=='done':
                        ret.append([pick['jld'][2].tolist(),
                                    pick['jld'][3].tolist()])
                    else:
                        ready = False
            else:
                ready = False
        if ready:
            return  HttpResponse(json.dumps({'status': 'done', 'jld': ret}), content_type='application/json')
        else:
            return HttpResponse(json.dumps("computing"), content_type='application/json')

    
    
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

def compute_hash2(h1, h2):
    """Returns the concatenation of two hashes"""
    return compute_hash(h1)+compute_hash(h2)

def get_unused_namepage():
    """Function returns an cool name for an analysis. Checks that it doesn't
    already exist. Requires the haikunator plugin."""
    
    new_analysis = False
    while not new_analysis:
        with transaction.atomic():
            url_basename = haikunator.haikunate()
            if not Analysis.objects.filter(url_basename=url_basename).exists():
                break
    return url_basename
