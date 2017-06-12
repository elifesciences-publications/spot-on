# Index of views for the fastSPT-GUI app (sockets side)
# A graphical user interface to the fastSPT tool by Anders S. Hansen, 2016
# By MW, GPLv3+, Feb.-Apr. 2017
#
# Here we store views that are routes for the second tab (corresponding to the
# ModelingController in Angular.

# === Imports
import fitted_zcor

# ==== Initialization
# careful a similar code exists in views.py
paths = {0: "./SPTGUI/fit_zcorr/0gaps",
         1: "./SPTGUI/fit_zcorr/1gaps",
         2: "./SPTGUI/fit_zcorr/2gaps"}
tree_init = fitted_zcor.init(paths=paths)

# ==== Functions (called from socket)
def get_fitted_zcor(message, data, url_basename):
    """Wrapper function to collect the object containing the filename of
    the nearest pair of (a,b) coefficients required to estimate the z correction
    to fit the jump length distribution"""
    return fitted_zcor.query_nearest(data['dT'], data['dZ'],
                                     int(data['GapsAllowed']), tree_init)
