angular.module('app')
    .service('downloadService', ['MainSocket', '$http', '$rootScope', function(MainSocket, $http, $rootScope){
	// This service handles $http requests to get the list for the datasets
	downloads = []

	this.getDownloads = function() {
	    var request = { type: "get_downloads" }
	    MainSocket.sendRequest(request).then(function(resp) {
		downloads = resp
		$rootScope.$broadcast('downloads:updated', resp);
	    })
	}
	
	// Add a download to the list of downloads
	this.setDownload = function(params) {
	    var request = { type: "set_download",
			    params: params }
	    MainSocket.sendRequest(request).then(function(resp) {
		if (resp.status == "success") {
		    console.log("Added download with id: "+resp.id)
		    params.do_id = resp.id
		    downloads.push(params)
		    $rootScope.$broadcast('downloads:updated', downloads)
		} else {
		    alert("Oops, something went wrong. We're sorry")
		}
	    })
	};

	this.deleteDownload = function(id) {
	    var request = { type: "del_download",
			    download_id: id }
	    return MainSocket.sendRequest(request)
	}

	// Send the request to get a figure
	this.download = function(params, fmt) {
	    request = { type: "get_download",
			format: fmt,
			download_id: params.do_id }
	    return MainSocket.sendRequest(request)
	}
	this.downloadAll = function(download_ids, celery_id) {
	    request = { type: "get_download_all",
			download_ids: download_ids,
			celery_id: celery_id}
	    return MainSocket.sendRequest(request)
	}
    }]);
