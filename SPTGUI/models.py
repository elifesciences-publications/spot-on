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


CHOICES_PREA = [('error', 'An unknown error occurred'),
                ('na', 'Not available'),
                ('error', 'An error occured'),
                ('queued', 'Sent to the processing queue'),
                ('uploaded', 'Uploaded done'),
                ('inprogress', 'Preprocessing in progress'),
                ('fileformaterror', 'Unrecognized file format'),
                ('ok', 'Preprocessing completed with success')]

class Dataset(models.Model):
    """Contains datasets and some data about the dataset"""
    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=2000)
    data = models.FileField(upload_to='uploads/', default='default.jpg', null=True, blank=True)
    parsed = models.FileField(upload_to='uploads/', null=True, blank=True)
    jld = models.FileField(upload_to='uploads/', null=True, blank=True)    
    unique_id = models.CharField(default='', max_length=200)
    upload_status = models.BooleanField(default=False)
    preanalysis_status = models.CharField(default='na', choices=CHOICES_PREA, max_length=100)
    preanalysis_token = models.CharField(default='', max_length=100)

    ## Preanalysis statistics
    pre_ntraces = models.IntegerField(null=True, blank=True)
    pre_ntraces3 = models.IntegerField(null=True, blank=True)
    pre_npoints = models.IntegerField(null=True, blank=True)
    pre_njumps = models.IntegerField(null=True, blank=True)
    pre_nframes = models.IntegerField(null=True, blank=True)
    pre_median_length_of_trajectories = models.FloatField(null=True, blank=True)
    pre_mean_length_of_trajectories = models.FloatField(null=True, blank=True)
    pre_median_particles_per_frame = models.FloatField(null=True, blank=True)
    pre_mean_particles_per_frame = models.FloatField(null=True, blank=True)
    pre_median_jump_length = models.FloatField(null=True, blank=True)
    pre_mean_jump_length = models.FloatField(null=True, blank=True)

class Download(models.Model):
    """Contain instructions for a download"""
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE) 
    params = models.FileField(upload_to='downloads/', null=True, blank=True)
    data = models.FileField(upload_to='downloads/', null=True, blank=True)
    export_svg = models.FileField(upload_to='downloads/', null=True, blank=True)
    export_eps = models.FileField(upload_to='downloads/', null=True, blank=True)
    export_png = models.FileField(upload_to='downloads/', null=True, blank=True)
    export_zip =  models.FileField(upload_to='downloads/', null=True, blank=True)
    
    status_svg = models.CharField(default='na', choices=CHOICES_PREA, max_length=100)
    status_eps = models.CharField(default='na', choices=CHOICES_PREA, max_length=100)
    status_png = models.CharField(default='na', choices=CHOICES_PREA, max_length=100)
    status_zip = models.CharField(default='na', choices=CHOICES_PREA, max_length=100)
