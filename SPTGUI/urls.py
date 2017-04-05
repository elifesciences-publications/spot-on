from django.conf.urls import url

from . import views

app_name =  'SPTGUI'

urlpatterns = [
    ## Debug routes
    #url(r'^upload/tmp/$', views.upload_tmp, name='upload_tmp'),    ## TEMPORARY
    #url(r'^upload/$', views.upload_tmp_bknd, name='upload_tmp_bknd'),    ## TEMPORARY
    #url(r'^queue/status/$', views.queue_status, name='queue_status'),## TEMPORARY
    #url(r'^queue/new/$', views.queue_new, name='queue_new'),## TEMPORARY
    url(r'^barchart/$', views.barchart, name='barchart'),## TEMPORARY
    
    ## Main routes
    url(r'^analysis/$', views.analysis_root, name='analysis_root'),
    url(r'^analysis/(?P<url_basename>.+)/upload/$', views.upload, name='upload'),
    url(r'^analysis/(?P<url_basename>.+)/api/datasets/$', views.datasets_api, name='datasets_api'),

    ## Information about a dataset
url(r'^analysis/(?P<url_basename>.+)/datasets/(?P<dataset_id>[0-9]+)/original/$', views.dataset_original, name='dataset_original'),
    url(r'^analysis/(?P<url_basename>.+)/datasets/(?P<dataset_id>[0-9]+)/parsed/$', views.dataset_parsed, name='dataset_parsed'),
    url(r'^analysis/(?P<url_basename>.+)/datasets/(?P<dataset_id>[0-9]+)/report/$', views.dataset_report, name='datasets_report'),

    ## Statistics
    url(r'^analysis/(?P<url_basename>.+)/statistics/$', views.statistics, name='statistics'),
    
    ## CRUD datasets
    url(r'^analysis/(?P<url_basename>.+)/api/delete/$', views.delete_api, name='delete_api'),
    url(r'^analysis/(?P<url_basename>.+)/api/edit/$', views.edit_api, name='edit_api'),
    url(r'^analysis/(?P<url_basename>.+)/api/preprocessing/$', views.preprocessing_api, name='preprocessing_api'),

    ## Perform analysis
    url(r'^analysis/(?P<url_basename>.+)/api/analyze/$', views.analyze_api, name='analyze_api'),
    url(r'^analysis/(?P<url_basename>.+)/api/analyze/(?P<dataset_id>[0-9]+)$', views.get_analysis, name='get_analysis'),
    
    url(r'^analysis/(?P<url_basename>.+)/', views.analysis, name='analysis'),
    url(r'^$', views.index, name='index'),
]
