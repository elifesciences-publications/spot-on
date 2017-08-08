from SPTGUI import views, views_email
"""fastSPT URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'^$', views.index),
    url(r'^SPTGUI/', include('SPTGUI.urls')),
    url(r'^admin/', admin.site.urls),
    ##
    ## ==== Email (these routes are duplicated in SPTGUI/urls.py)
    ##
    url(r'^email/subscribe/$', views_email.email, name='email_subscribe'),
    url(r'^email/unsubscribe/(?P<token>.+)$',views_email.email_unsubscribe, name='email_unsubscribe'),
    url(r'^email/confirm/(?P<token>.+)$', views_email.email, name='email_confirm'),
]
