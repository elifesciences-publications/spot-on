# Index of views for the fastSPT-GUI app (sockets side)
# A graphical user interface to the fastSPT tool by Anders S. Hansen, 2016
# By MW, GPLv3+, Feb.-Apr. 2017
#
# Here we store views that are routes for the last tab (corresponding to the
# SettingsController in Angular.
from .models import Analysis
from django.core.urlresolvers import reverse

def erase(message, data, url_basename):
    """Erase an analysis. There is no way back"""
    Analysis.objects.get(url_basename=url_basename).delete()
    return reverse('SPTGUI:index')
