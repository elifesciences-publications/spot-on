from django.shortcuts import render
from .models import Analysis, Dataset

import random, string

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
