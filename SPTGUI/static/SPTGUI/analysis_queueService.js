angular.module('app')
    .factory('ProcessingQueue', ['MainSocket', '$q', '$interval', '$rootScope', '$timeout', function(MainSocket, $q, $interval, $rootScope, $timeout) {
	var Service = {};
	celery_ids = []
	
	addToQueue =  function(celery_id, queue, callback, params) {
	    defer = $q.defer();
	    celery_ids.push({celery_id: celery_id,
			     queue: queue,
			     callback: callback,
			     params: params,
			     memory: null,
			     cb: defer,
			     resolved: false})
	    console.log("Added id: " + celery_id + " to the polling queue")
	    return defer.promise
	}
	Service.addToQueue = addToQueue

	pollQueue = function(celery_ids) {
	    var request = {type: "poll_queue",
			   queue_type:celery_ids.map(function(el){return el.queue}),
			   celery_ids: celery_ids.map(function(el){return el.celery_id;})}
	    return MainSocket.sendRequest(request); 
	}

	$interval(function() { 
	    if (celery_ids.length>0) {
		clids = angular.copy(celery_ids)
		pollQueue(clids).then(function(resp) {
		    rem = []
		    if (resp.length==clids.length) {
			resp.forEach(function(el,i) {
			    if (clids[i].memory != el){
				if (clids[i].callback) {
		 		    clids[i].callback(el, clids[i].params)
				    clids[i].memory = el
				}
			    }
			    if (el=='OK') { // resolve promise
				rem.push({celery_id: clids[i].celery_id, ok: true})
			    } else if (el=='FAILURE') {
				console.log('Job failed:'+  clids[i]);
				rem.push({celery_id: clids[i].celery_id, ok: false})
			    }
			})
		    }
		    
		    if (rem.length>0) { // remove ids from the list
			$timeout(function() {
			    rem.forEach(function(el)  {
				clids = clids.map(function(ell) {
				    if (ell.celery_id == el.celery_id) {
					if (el.ok) {
					    ell.cb.resolve(ell.memory)
					}
					ell.resolved = true
				    }
				    return ell
				})
			    })
			    celery_ids = clids.filter(function(el) {
				return !el.resolved
			    })
			})
		    }
		})
	    }
	}, 500) // Could be moved to 500 when not debugging
	return Service;
    }]);
