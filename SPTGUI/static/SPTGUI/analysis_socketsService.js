angular.module('app')
    .factory('MainSocket', ['$q', '$rootScope', function($q, $rootScope) {
	// We return this object to anything injecting our service
	var Service = {};
	// Keep all pending requests here until they get responses
	var callbacks = {};
	// Create a unique callback ID to map requests to responses
	var currentCallbackId = 0;
	// Create our websocket object with the address to the websocket

    // When we're using HTTPS, use WSS too.
	var ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
	var url = ws_scheme + '://' + window.location.host + window.location.pathname;
	if (url.substr(-1) != '/') url += '/';
	var ws = new ReconnectingWebSocket(url + 'ws');
	//var ws = new WebSocket(ws_scheme + '://' + window.location.host + window.location.pathname + 'ws');	
	ws.onopen = function(){
	    $rootScope.$broadcast('socket:ready');	    
	};
	
	ws.onmessage = function(message) {
            listener(JSON.parse(message.data));
	};

	sendRequest = function(request) {
	    var defer = $q.defer();
	    var callbackId = getCallbackId();
	    callbacks[callbackId] = {
		time: new Date(),
		cb:defer
	    };
	    request.callback_id = callbackId;
	    //console.log('Sending request', request);
	    ws.send(JSON.stringify(request));
	    return defer.promise;
	}
	Service.sendRequest = sendRequest

	function listener(data) {
	    var messageObj = data;
	    //console.log("Received data from websocket: ", messageObj);
	    // If an object exists with callback_id in our callbacks object, resolve it
	    if(callbacks.hasOwnProperty(messageObj.callback_id)) {
		//console.log(callbacks[messageObj.callback_id]);
		$rootScope.$evalAsync(callbacks[messageObj.callback_id].cb.resolve(messageObj.data));
		//$rootScope.$apply(callbacks[messageObj.callback_id].cb.resolve(messageObj.data));
		delete callbacks[messageObj.callbackID];
		
	    }
	}
	// This creates a new callback ID for a request
	function getCallbackId() {
	    currentCallbackId += 1;
	    if(currentCallbackId > 10000) {
		currentCallbackId = 0;
	    }
	    return currentCallbackId;
	}

	return Service;
    }])
