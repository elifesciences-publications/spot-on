angular.module('app')
    .controller('DownloadController', ['downloadService', 'ProcessingQueue', '$scope', '$interval', '$window', function(downloadService, ProcessingQueue, $scope, $interval, $window) {

	// ==== Initialize variables (populated when the socket is ready)
	$scope.downloads = []
	var datasets = null;
	socketReady = false // not to double initialize after lost connexion
	$scope.$on('socket:ready', function() {
	    console.log("Getting the list of analyses saved for download")
	    downloadService.getDownloads()
	})
	
	// ==== Launch this function each time the downloads variable is updated
	$scope.$on('downloads:updated', function(event, downloads) {
	    $scope.downloads = downloads
	})

	$scope.$on('datasets:updated', function(event, data) {
	    datasets = data;
	})

	// ==== The binding function
	$scope.downloadFigure = function(dwnl_id, format) {
	    params = angular.copy(downloads[dwnl_id]);
	    downloadService.download(params, format).then(function(resp) {
		if (resp.celery_id) {
		    ProcessingQueue.addToQueue(resp.celery_id, 'download').then(function(resp2){
			downloadService.download(params, format)
			    .then(function(resp3){
				if (resp3.status=="success") {
				    console.log("Download ready at "+resp3.url)
				    $window.open('/static/SPTGUI/downloads/'+resp3.url, "_blank");
				} else {
				    alert("Oops, something went wrong")
				}
			    })
		    })
		} else if (resp.status == "success") {
		    console.log("Download already ready")
		    $window.open('/static/SPTGUI/downloads/'+resp.url, "_blank");
		} else {
		    alert("Oops, something went wrong")
		    console.log(resp.status)
		}
	    })
	};

	//
	// ==== Basic CRUD operations
	// 
	$scope.deleteDownload = function(do_id) {
	    console.log("Deleting download with id: "+ do_id)
	    downloadService.deleteDownload(do_id).then(function(resp) {
		if (resp.status=="success") {
		    console.log("Download deleted: "+do_id)
		    $scope.downloads = $scope.downloads.filter(function(el){
			return el.do_id != do_id
		    })
		}
		else {alert("Something went wrong")}
	    })
	}

	// Get information about the included datasets
	$scope.getDatasetInfo = function(idx, option) {
	    if (!option|datasets===null) {return}
	    da = angular.copy(datasets)
	    da = da.map(function(el, i){el.i = i; return el})
	    var dai = da.filter(function(el) {return el.id==idx})[0]
	    return dai[option]
	}
	$scope.getDisplay = function(dwl) {
	    console.log(dwl)
	}
    }]);
