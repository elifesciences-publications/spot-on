angular.module('app')
    .service('downloadService', ['$http', '$rootScope', function($http, $rootScope){
	// This service handles $http requests to get the list for the datasets
	downloads = []
	
	getDownloads().then(function(dataResponse) {
	    downloads = dataResponse.data
	    alert('downloads initialized')
	    $rootScope.$broadcast('downloads:updated', downloads)
	})
	
	
	this.getDownloads = function() {
	    return $http.get('./api/download/')
	}

	// Add a download to the list of downloads
	this.setDownload = function(params) {
	    downloads.push(params)
	    // Send a POST with the download and get back the download id
	    $rootScope.$broadcast('downloads:updated', downloads)
	};

	// Send the request to get a figure
	this.download = function(params, fmt) {
	    params.format = fmt
	    return $http.post('./api/download/', params)
	}

	this.checkDownload = function(download_id, format) {
	    return $http.get('./api/download/'+download_id+'/'+format)
	}
    }]);
