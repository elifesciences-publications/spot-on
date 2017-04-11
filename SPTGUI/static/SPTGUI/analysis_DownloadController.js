angular.module('app')
    .controller('DownloadController', ['downloadService', '$scope', '$interval', '$window', function(downloadService, $scope, $interval, $window) {

	// ==== Initialize variables
	$scope.downloads = []

	// ==== Launch this function each time the downloads variable is updated
	$scope.$on('downloads:updated', function(event, downloads) {
	    $scope.downloads = downloads
	})

	$scope.intervalRunning = false;
	
	interval = $interval(function() {
	    if (!$scope.intervalRunning) {return false;}
	    downloadService.checkDownload($scope.tmpId, $scope.tmpFormat)
		.then(function(dataR) {
		    if (dataR.data.status=='success') {
			$scope.intervalRunning = false;
			$window.open('/static/SPTGUI/downloads/'+dataR.data.url, "_blank");
		    }
		})

	}, 500);


	// ==== The binding function
	$scope.downloadFigure = function(dwnl_id, format) {
	    $scope.tmpFormat = format;
	    downloadService.download($scope.downloads[dwnl_id], $scope.tmpFormat).then(function(data) {
		if (data.data.status != 'success') {
		    alert('something went wrong with the download')
		} else {
		    $scope.tmpId = data.data.id
		    $scope.intervalRunning = true;
		};
	    })
	};

    }]);
