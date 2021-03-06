# Index of sockets routes for the fastSPT-GUI app
# A graphical user interface to the fastSPT tool by Anders S. Hansen, 2016
# By MW, GPLv3+, Feb.-Apr. 2017

## ==== Imports
import json, logging
from channels import Group
from channels.sessions import channel_session
import sockets_tab_data, sockets_download, sockets_kinetics, sockets_settings, sockets_upload

## This is the most important part of this script, since it defines the matching
##+between the commands received by the socket and the corresponding functions.
routes = {'list_datasets' : sockets_tab_data.list_datasets,
          'edit_dataset'  : sockets_tab_data.edit_api,
          'global_statistics': sockets_tab_data.global_statistics,
          'poll_queue': sockets_tab_data.poll_queue,
          'get_fitted_zcor': sockets_kinetics.get_fitted_zcor,
          #'get_pooled_jld': sockets_kinetics.get_pooled_jld,
          'set_download': sockets_download.set_download,
          'set_download': sockets_download.set_download,
          'get_downloads': sockets_download.get_downloads,
          'get_download': sockets_download.get_download,
          'get_download_all': sockets_download.get_download_all,
          'del_download': sockets_download.del_download,
          'list_formats': sockets_upload.list_formats,
          'erase': sockets_settings.erase}

@channel_session
def ws_connect(message):
    url_basename =  message['path'].split('/')[-2]
    message.reply_channel.send({'accept': True}) # Accept connexion from the socket
    message.channel_session['url_basename'] = url_basename

@channel_session
def ws_receive(message):
    """This function is a callback ran each time the socket receives a message"""
    try:
        data = json.loads(message['text'])
    except ValueError:
        logging.debug("ws message isn't json text=%s", text)
        return
    if 'type' not in data:
        logging.debug("ws message unexpected format data=%s", data)
        return

    url_basename = message.channel_session['url_basename']
    if data: ## Parse the input
        res = routes[data['type']](message, data, url_basename)
        out = {'type': data['type'],
               'callback_id': data['callback_id'],
               'data' : res}
        message.reply_channel.send({'text': json.dumps(out)})
    
@channel_session
def ws_disconnect(message):
    pass

