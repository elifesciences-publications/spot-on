angular.module('app')
    .service('getterService', ['MainSocket', '$http', '$rootScope', function(MainSocket, $http, $rootScope) {
	// The purpose of this service is to retrieve the list of uploaded datasets
	// It used to rely on Ajax request but it is now moving to Sockets!
	this.getDatasets2 = function() {
	    var request = { type: "list_datasets" }
	    var promise = MainSocket.sendRequest(request); 
	    return promise;
	}

	this.updateDataset = function(idd, dataset) {
	    var request = { type: "edit_dataset" ,
			    dataset_id: idd,
			    dataset: dataset}
	    return MainSocket.sendRequest(request); 
	}

	this.getGlobalStatistics = function() {
	    var request = { type: "global_statistics" }
	    var promise = MainSocket.sendRequest(request); 
	    return promise;
	}
	// Get the nearest fitted z correction
	this.getNearestZcorr = function(dZ, dT, GapsAllowed) {
	    return MainSocket.sendRequest({type: "get_fitted_zcor",
					   dT: dT, dZ: dZ, GapsAllowed:GapsAllowed})
	}

	// Get the list of accepted file formats
	this.getFileFormats = function() {
	    return MainSocket.sendRequest({type: "list_formats"})
	}

	// Fired when all the datasets have been loaded ($scope.datasets exists)
	this.broadcastLoadedDatasets = function(datasets) {
	    $rootScope.$broadcast('datasets:loaded', datasets);
	    $rootScope.$broadcast('datasets:updated', datasets)	    
	}

	this.broadcastAddedDatasets =  function(datasets) {
	    $rootScope.$broadcast('datasets:added', datasets);
	    $rootScope.$broadcast('datasets:updated', datasets)	    
	    console.log("Added dataset. Number of datasets: "+datasets.length);
	}

	this.broadcastEditedDataset =  function(dataset_id, dataset) {
	    $rootScope.$broadcast('dataset:updated', dataset_id, dataset)	    
	}
	
	
	this.broadcastDeletedDataset =  function(database_id,dataset_id, datasets) {
	    $rootScope.$broadcast('datasets:deleted',{database_id: database_id,
						      dataset_id: dataset_id});
	    $rootScope.$broadcast('datasets:updated', datasets)
	}
		
	// Delete a dataset, provided its id (filename used for validation)
	this.deleteDataset = function(database_id, filename) {
	    console.log("Deprecated call to deleteDataset");
	    return $http.post('./api/delete/',
			      {'id': database_id,
			       'filename': filename});
	};

	this.getPreprocessing = function(callback) {
	    console.log("Deprecated call to getPreprocessing");
	    return $http.get('./api/preprocessing/');
	};
    }])
