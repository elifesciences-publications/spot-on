angular.module('app')
    .service('getterService', ['MainSocket', '$http', '$rootScope', function(MainSocket, $http, $rootScope) {
	// The purpose of this service is to retrieve the list of uploaded datasets
	// It used to rely on Ajax request but it is now moving to Sockets!
	
	this.getDatasets2 = function() {
	    var request = { type: "list_datasets" }
	    var promise = MainSocket.sendRequest(request); 
	    return promise;
	}

	this.getGlobalStatistics = function() {
	    var request = { type: "global_statistics" }
	    var promise = MainSocket.sendRequest(request); 
	    return promise;
	}

	// Fired when all the datasets have been loaded ($scope.datasets exists)
	this.broadcastLoadedDatasets = function(data) {
	    $rootScope.$broadcast('datasets:loaded', data);
	}

	this.broadcastAddedDatasets =  function(datasets) {
	    $rootScope.$broadcast('datasets:added', vdatasets);
	    console.log("Added dataset signal: "+datasets.length);
	}
	
	this.broadcastDeletedDataset =  function(database_id,dataset_id) {
	    $rootScope.$broadcast('datasets:deleted',{database_id: database_id,
						      dataset_id: dataset_id});
	}
	
	this.getDatasets = function(callback) {
	    console.log('getterService.getDatasets is deprecated. Use the socket');
	    return $http.get('./api/datasets/');
	};

	// Get some statistics on the uploaded and preprocessed datasets
	this.getStatistics = function(callback) {
	    console.log('getterService.getStatistics is deprecated. Use the socket');
	    return $http.get('./statistics/');
	};
		
	// Delete a dataset, provided its id (filename used for validation)
	this.deleteDataset = function(database_id, filename) {
	    return $http.post('./api/delete/',
			      {'id': database_id,
			       'filename': filename});
	};

	this.updateDataset = function(database_id, dataset) {
	    console.log('getterService.updateDataset is deprecated. Use the socket');
	    return $http.post('./api/edit/',
			      {'id': database_id,
			       'dataset': dataset});
	};

	this.getPreprocessing = function(callback) {
	    return $http.get('./api/preprocessing/');
	};
	
	this.broadcastDataset = function(datasets) {
	    // Broadcast a message that a dataset has been edited
	    console.log("DEPRECATED: Broadcaster 'updated' dataset. ")
	    $rootScope.$broadcast('datasets:updated',datasets);
	};
	
    }])
