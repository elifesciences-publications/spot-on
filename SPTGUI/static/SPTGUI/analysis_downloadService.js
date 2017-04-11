angular.module('app')
    .service('downloadService', ['$http', '$rootScope', function($http, $rootScope){
	// This service handles $http requests to get the list for the datasets
	downloads = []

	// Add a download to the list of downloads
	this.setDownload = function(params) {
	    downloads.push(params)
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
