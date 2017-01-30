from __future__ import unicode_literals

from django.db import models

# Create your models here.
class Analysis(models.Model):
    """This is the main object to be manipulated. 
    It is the container of the analysis app page."""
    
    url_basename = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=2000)

    
class Dataset(models.Model):
    """Contains datasets and some data about the dataset"""
    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=2000)
    data = models.FileField(upload_to='uploads/')
    
