from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from django.template import loader

def index(request):
    template = loader.get_template('SPTGUI/homepage.html')
    return HttpResponse(template.render(request))
    #return HttpResponse("Hello, world. This is the main page, hihi.")
