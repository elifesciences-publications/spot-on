angular.module('app')
    .service('getterService', ['$http', '$rootScope', function($http, $rootScope) {
	// This service handles $http requests to get the list for the datasets
	this.getDatasets = function(callback) {
	    return $http.get('./api/datasets/');
	};

	// Get some statistics on the uploaded and preprocessed datasets
	this.getStatistics = function(callback) {
	    return $http.get('./statistics/');
	};
	
	// Get some statistics on the uploaded and preprocessed datasets
	this.getJLD = function(dataset_id) {
	    return $http.get('./api/jld/'+dataset_id);
	};
	
	// Delete a dataset, provided its id (filename used for validation)
	this.deleteDataset = function(database_id, filename) {
	    return $http.post('./api/delete/',
			      {'id': database_id,
			       'filename': filename});
	};

	this.updateDataset = function(database_id, dataset) {
	    return $http.post('./api/edit/',
			      {'id': database_id,
			       'dataset': dataset});
	};

	this.getPreprocessing = function(callback) {
	    return $http.get('./api/preprocessing/');
	};
	
	this.broadcastDataset = function(datasets) {
	    // Broadcast a message that a dataset has been edited
	    $rootScope.$broadcast('datasets:updated',datasets);
	};
	
    }])
