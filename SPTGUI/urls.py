from django.conf.urls import url

from . import views

app_name =  'SPTGUI'

urlpatterns = [
    #url(r'^upload/tmp/$', views.upload_tmp, name='upload_tmp'),    ## TEMPORARY
    url(r'^analysis/$', views.analysis_root, name='analysis_root'),
    url(r'^analysis/(?P<url_basename>.+)/upload/$', views.upload, name='upload'),
    url(r'^analysis/(?P<url_basename>.+)/api/datasets/$', views.datasets_api, name='datasets_api'),
    url(r'^analysis/(?P<url_basename>.+)/$', views.analysis, name='analysis'),
    url(r'^$', views.index, name='index'),
]
