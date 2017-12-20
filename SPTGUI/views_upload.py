#-*-coding:utf-8-*-
# Index of views for the fastSPT-GUI app
# A graphical user interface to the fastSPT tool by Anders S. Hansen, 2016
# By MW, GPLv3+, Feb.-Apr. 2017
#
# Here we store views that relate to the upload of datasets

## ==== Imports
import os, json, pickle, random, hashlib, tempfile
import fileuploadutils2 as fuu
from flask import Response

from .models import Analysis, Dataset, PendingUploadAPI
from django.views.decorators.csrf import csrf_exempt
from django.core.files import File
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.utils import timezone
import fastSPT.custom_settings as custom_settings

from celery import celery
import tasks, import_tools


bf = "./static/analysis/" ## Location to save the fitted datasets
import_path = "./static/upload/"

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
        ## 0. Extract format/parser info
        fmt = request.POST['parserName']
        fmtParams = json.loads(request.POST['parserParams'])
        
        ## 1. Get the analysis object
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

        ## 3. Parameters and init to compute the JLD (if the celery task
        ##    `check_input_file` returns successfully.
        compute_params = custom_settings.compute_params
        pick = {'params' : compute_params,
                'jld' : None,
                'status' : 'queued'}
        cha = "03f9de26788d1c29" #'c0f7e565600c3bf5'
        pa = bf+"{}/jld_{}_{}.pkl".format(url_basename, cha, da.id)
        with open(pa, 'w') as f: ## Save that we are computing
            pickle.dump(pick, f)

        ## 3. Defer to the celery analysis
        da.preanalysis_status='queued'
        ta = celery.chain(
            tasks.check_input_file.s(da.data.path, da.id, fmt, fmtParams),
            tasks.compute_jld.s(pooled=False,
                                path=bf,
                                hash_prefix=cha,
                                compute_params=compute_params,
                                url_basename=url_basename,
                                default=True)).apply_async()

        da.preanalysis_token = ta.id
        da.save()
        rr = json.loads(res.content)
        rr['celery_id'] = [ta.parent.id, ta.id]
        res.content = json.dumps(rr)
    return res


## ==== TrackMate upload-related views
## Spot-On implements a simple API (accessible at /uploadapi/) in order to simply
##+interface with tracking softwares. Anyone is free to implement it, and it
##+should not break randomly.
## It works in two times:
##  1. A GET request is made to declare what will be uploaded (more details below)
##     Based on this request, the server decides whether or not it will allow the
##     upload. If the upload is allowed, it returns a simple token.
##  2. A POST request, containing the token and the data.
##  3. When the data has been totally uploaded:
##   a. The checksum of the file is checked
##   b. The file is added at the right location (either a new analysis is created,
##     +or the file is appended to an existing analysis.

@csrf_exempt
def uploadapi(request):
    """This route handles external upload requests. It can be disabled by setting
    UPLOADAPI_ENABLE = False in the custom_settings.py file."""

    ALLOWED_API_VERSIONS = ('1.0',)
    ALLOWED_FORMATS = ('trackmate',)
    TOKEN_LENGTH = 32
    BF="./static/analysis/"

    def answer(status, message, token="none", extra={}):
        return HttpResponse(json.dumps(dict(
            {"status": status,
             "message": message,
             "token": token}.items()+extra.items())))

    if not custom_settings.UPLOADAPI_ENABLE:
        return answer("denied", "The upload API is not activated in this server")

    if request.method == 'GET':
        ## Validate the GET
        if ('format' not in request.GET) or ('version' not in request.GET) or ('sha' not in request.GET) or ('url' not in request.GET): ## Missing parameters
            return answer("denied", "Missing parameters")
        if request.GET['version'] not in ALLOWED_API_VERSIONS: ## Version
            return answer("denied", "Unsupported version")
        if request.GET['format'] not in ALLOWED_FORMATS: ## Format
            return answer("denied", "Unsupported format")
        if not is_sha1(request.GET["sha"]):
            return answer("denied", "Invalid SHA1")
        if request.GET['url']=='new' and not custom_settings.UPLOADAPI_ENABLE_NEWANALYSIS:
            return answer("denied", "The creation of a new analysis is not allowed.")
        if request.GET['url']!='new' and not custom_settings.UPLOADAPI_ENABLE_EXISTINGANALYSIS:
            return answer("denied", "Uploading to an existing analysis is not allowed.")
        if request.GET['url']!='new' and Analysis.objects.filter(url_basename=request.GET['url']).count()==0:
            return answer("denied", "The specified analysis does not exist.")

        ## We cannot pre-reserve a name, so we just store "new" in the field
        ##+if we need to create a new analysis
        url_basename = request.GET['url']
        sha = request.GET['sha']
        fmt = request.GET['format']
        version = request.GET['version']

        ## Generate a new token
        token = get_new_hex_token(TOKEN_LENGTH)

        ## Create the PendingUpload entry in the database
        pu = PendingUploadAPI(token = token,
                              expectedSHA = sha,
                              fmt = fmt,
                              version = version,
                              url_basename = url_basename,
                              creation_date = timezone.now())
        pu.save()
        return answer("success", "Server ready to accept a {} file".format(fmt), token)

    elif request.method == 'POST':
        ## Handle the POSTed data
        
        ## Let's make preliminary checks    
        try:
            body = request.body#.decode('utf-8')
        except:
            return answer("failed", "Cannot read sequence")
        if len(body)<=TOKEN_LENGTH+3:
            return answer("failed", "Received empty file")
        token = body[:TOKEN_LENGTH]
        if body[TOKEN_LENGTH:(TOKEN_LENGTH+2)] != "||" or not is_sha1(token, 32):
            return answer("failed", "Misformed request")

        ## Let's see if the token exists
        pu_rq = PendingUploadAPI.objects.filter(token=token)
        if pu_rq.count() != 1:
            return answer("failed", "Unknown token")
        pu = pu_rq[0]

        ## Check SHA1
        rst = body[(TOKEN_LENGTH+2):]
        if hashlib.sha1(rst).hexdigest() != pu.expectedSHA:
            return answer("failed", "Corrupted file")

        ## Make sure the analysis exists, or create it if it doesn't exist
        url_basename = pu.url_basename
        if url_basename == 'new':
            url_basename = import_tools.get_unused_namepage()
            ana = Analysis(url_basename=url_basename,
                           pub_date=timezone.now(),
                           name='',
                           description='')
            ana.save()
        else:
            ana = Analysis.objects.get(url_basename = url_basename)
        BFpath = os.path.join(BF,url_basename)
        if not os.path.isdir(BFpath):
            os.makedirs(BFpath)
            
        ## Perform the import
        name = "TMPNAME"
        f = tempfile.NamedTemporaryFile(dir=import_path, delete=False)
        f.write(rst.replace("µm", "micron"))
        fi = File(f)
        try:
            import_tools.import_dataset(fi, name, ana,
                                        url_basename, bf=bf,
                                        fmt="trackmate",
                                        fmtParams={"format": "xml", "framerate":-1})
        except:
            return answer("failed", "the file could not be processed")

        full_url = custom_settings.URL_BASENAME + reverse('SPTGUI:analysis', args=[url_basename])
        print "A new analysis has been uploaded on: {}".format(full_url)
        return answer("success",
                      "A POST request has been received",
                      extra={"url": full_url})

## ==== Private methods
def get_hex_token(n):
    """Returns a 32-character hexadecimal token"""
    return '%030x' % random.randrange(16**n)

def get_new_hex_token(n=32):
    """Returns a token that has never been attributed"""
    tok = get_hex_token(n)
    while PendingUploadAPI.objects.filter(token=tok).count()!=0:
        tok = get_hex_token(n)
    return tok
            
def is_sha1(maybe_sha, n=40):
    """Returns True if the maybe_sha could be a SHA
    from: https://stackoverflow.com/a/32234251"""
    if len(maybe_sha) != n:
        return False
    try:
        sha_int = int(maybe_sha, 16)
    except ValueError:
        return False
    return True
