from . import sockets

channel_routing = {
    'websocket.connect': sockets.ws_connect,
    'websocket.receive': sockets.ws_receive,
    'websocket.disconnect': sockets.ws_disconnect,
}

