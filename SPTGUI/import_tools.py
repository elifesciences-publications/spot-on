import pickle
from django.db import transaction
from .models import Analysis
from haikunator import Haikunator
from SPTGUI.models import Dataset
import fastSPT.custom_settings as custom_settings
import SPTGUI.tasks as tasks

haikunator = Haikunator()

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

def import_dataset(fi, name, ana, url_basename, bf, fmt, fmtParams={}):
    ## Create the dataset
    da = Dataset(analysis=ana,
                 name=name,
                 description='Demo dataset',
                 unique_id = 0,
                 upload_status=True, # Upload is complete
                 preanalysis_status='uploaded', # Preanalysis not launched
                 data=fi)
    da.save()

    ## Precompute JLD
    compute_params = custom_settings.compute_params
    pick = {'params' : compute_params,
            'jld' : None,
            'status' : 'queued'}
    cha = "03f9de26788d1c29" #'c0f7e565600c3bf5'
    pa = bf+"{}/jld_{}_{}.pkl".format(url_basename, cha, da.id)
    with open(pa, 'w') as f: ## Save that we are computing
        pickle.dump(pick, f)
    tasks.check_input_file(da.data.path, da.id, fmt, fmtParams, queue=False)
    tasks.compute_jld(da.id,
                      pooled=False,
                      path=bf,
                      hash_prefix=cha,
                      compute_params=compute_params,
                      url_basename=url_basename,
                      default=True, queue=False)
