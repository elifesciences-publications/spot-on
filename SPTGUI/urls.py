from django.conf.urls import url

from . import views

app_name =  'SPTGUI'

urlpatterns = [
    #url(r'^upload/tmp/$', views.upload_tmp, name='upload_tmp'),    ## TEMPORARY
    url(r'^queue/status/$', views.queue_status, name='queue_status'),## TEMPORARY
    url(r'^queue/new/$', views.queue_new, name='queue_new'),## TEMPORARY
    url(r'^analysis/$', views.analysis_root, name='analysis_root'),
    url(r'^analysis/(?P<url_basename>.+)/upload/$', views.upload, name='upload'),
    url(r'^analysis/(?P<url_basename>.+)/api/datasets/$', views.datasets_api, name='datasets_api'),
    url(r'^analysis/(?P<url_basename>.+)/api/delete/$', views.delete_api, name='delete_api'),
    url(r'^analysis/(?P<url_basename>.+)/api/edit/$', views.edit_api, name='edit_api'),
    url(r'^analysis/(?P<url_basename>.+)/api/preprocessing/$', views.preprocessing_api, name='preprocessing_api'),
    url(r'^analysis/(?P<url_basename>.+)/$', views.analysis, name='analysis'),
    url(r'^$', views.index, name='index'),
]
