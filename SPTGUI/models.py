from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible
from django.db import models
from django.shortcuts import redirect
from django.core.urlresolvers import reverse


@python_2_unicode_compatible
class Analysis(models.Model):
    """This is the main object to be manipulated. 
    It is the container of the analysis app page."""
    
    url_basename = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')
    acc_date = models.DateTimeField('date accessed', null=True, blank=True)
    mod_date = models.DateTimeField('date modified', null=True, blank=True)
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=2000)
    editable = models.BooleanField(default=True)
    
    def __str__(self):
        return self.url_basename
    def get_absolute_url(self):
        return reverse("SPTGUI:analysis", args=[self.url_basename])

CHOICES_PREA = [('error', 'An unknown error occurred'),
                ('na', 'Not available'),
                ('error', 'An error occured'),
                ('queued', 'Sent to the processing queue'),
                ('uploaded', 'Uploaded done'),
                ('inprogress', 'Preprocessing in progress'),
                ('fileformaterror', 'Unrecognized file format'),
                ('ok', 'Preprocessing completed with success')]

@python_2_unicode_compatible
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
    import_report = models.TextField(null=True, blank=True)

    ## Preanalysis statistics
    dt = models.FloatField(null=True, blank=True)
    pre_ngaps = models.IntegerField(null=True, blank=True)
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

    def __str__(self):
        return "{} ({})".format(self.name, self.analysis.url_basename)
    
class Download(models.Model):
    """Contain instructions for a download"""
    bf = 'SPTGUI/static/SPTGUI/downloads'
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE) 
    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE)
    pub_date = models.DateTimeField('date created')
    description =  models.CharField(default='', max_length=400)
    name =  models.CharField(default='', max_length=200)
    
    params = models.FileField(upload_to=bf, null=True, blank=True)
    data = models.FileField(upload_to=bf, null=True, blank=True)
    export_svg = models.FileField(upload_to=bf, null=True, blank=True)
    export_eps = models.FileField(upload_to=bf, null=True, blank=True)
    export_pdf = models.FileField(upload_to=bf, null=True, blank=True)
    export_png = models.FileField(upload_to=bf, null=True, blank=True)
    export_zip =  models.FileField(upload_to=bf, null=True, blank=True)
    
    status_svg = models.CharField(default='na', choices=CHOICES_PREA, max_length=100)
    status_eps = models.CharField(default='na', choices=CHOICES_PREA, max_length=100)
    status_png = models.CharField(default='na', choices=CHOICES_PREA, max_length=100)
    status_pdf = models.CharField(default='na', choices=CHOICES_PREA, max_length=100)
    status_zip = models.CharField(default='na', choices=CHOICES_PREA, max_length=100)

class Email(models.Model):
    """Contains people registering to the newsletter. For privacy reasons,
    these are not linked to the uploaded analyses."""

    email = models.CharField(default='', max_length=1000)
    validated = models.BooleanField(default=False)
    token = models.CharField(default='', max_length=256)
    add_date = models.DateTimeField('date created')
    validation_date = models.DateTimeField('date validated', null=True, blank=True)
    
