from django.conf.urls import url

from . import views

app_name =  'SPTGUI'

urlpatterns = [
    url(r'^analysis/$', views.analysis_root, name='analysis_root'),    
    url(r'^analysis/(?P<url_basename>.+)/$', views.analysis, name='analysis'),
    url(r'^$', views.index, name='index'),
]
