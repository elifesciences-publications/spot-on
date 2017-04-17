angular.module('app')
    .controller('DownloadController', ['downloadService', 'ProcessingQueue', '$scope', '$interval', '$window', function(downloadService, ProcessingQueue, $scope, $interval, $window) {

	// ==== Initialize variables (populated when the socket is ready)
	$scope.downloads = []
	

	// ==== Launch this function each time the downloads variable is updated
	$scope.$on('downloads:updated', function(event, downloads) {
	    $scope.downloads = downloads
	})

	// $scope.intervalRunning = false;
	
	// interval = $interval(function() {
	//     if (!$scope.intervalRunning) {return false;}
	//     downloadService.checkDownload($scope.tmpId, $scope.tmpFormat)
	// 	.then(function(dataR) {
	// 	    if (dataR.data.status=='success') {
	// 		$scope.intervalRunning = false;
	// 		$window.open('/static/SPTGUI/downloads/'+dataR.data.url, "_blank");
	// 	    }
	// 	})
	// }, 500);


	// ==== The binding function
	$scope.downloadFigure = function(dwnl_id, format) {
	    params = angular.copy(downloads[dwnl_id]);
	    downloadService.download(params, format).then(function(resp) {
		if (resp.celery_id) {
		    ProcessingQueue.addToQueue(resp.celery_id, 'download').then(function(resp2){
			downloadService.download(params, format)
			    .then(function(resp3){
				if (resp3.status=="success") {
				    console.log("Download ready")
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
		}
	    })
	};

    }]);
