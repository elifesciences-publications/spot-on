# Index of views for the fastSPT-GUI app (sockets side)
# A graphical user interface to the fastSPT tool by Anders S. Hansen, 2016
# By MW, GPLv3+, Feb.-Apr. 2017
#
# Here we store views that are routes for the first tab (corresponding to the
# UploadController in Angular.

##
## ==== Imports
##
import parsers


##
## ==== Views
##
def list_formats(message, data, url_basename):
    """List the accepted formats"""
    return parsers.list_formats()
