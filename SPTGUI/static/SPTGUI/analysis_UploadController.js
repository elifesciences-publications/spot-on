angular.module('app')
    .controller('UploadController', ['getterService', '$scope', '$cookies', '$interval', function(getterService, $scope, $cookies, $interval) {
	// This is the controller for the upload part of the app

	//
	// ==== Let's first define some global variables (on the $scope).
	//
	$scope.currentlyUploading=false;
	$scope.successfullyUploaded=0;
	$scope.editingDataset=false;
	$scope.editedDataset=null;
	$scope.poolPreprocessing=false;
	$scope.random = 0; // DEBUG
	//$scope.statistics = null;
	
	$scope.uploadStart = function($flow){
	    $flow.opts.headers =  {'X-CSRFToken' : $cookies.get("csrftoken")};
	}; // Populate $flow with the CSRF cookie!
	getterService.getDatasets().then(function(dataResponse) {
	    $scope.datasets = dataResponse['data'];
	    $scope.successfullyUploaded=dataResponse['data'].length;
	}); // Populate the scope with the already uploaded datasets
	getterService.getStatistics().then(function(dataResponse) {
	    $scope.statistics = dataResponse['data'];
	}); // Populate the scope with the already computed statistics

	$scope.showingStatistics=false;
	$scope.shownStatistics=null;
	
	
	//
	// ==== Handle the edition of the list of files
	//
	$scope.deleteDataset = function(dataset) {
	    getterService.deleteDataset(dataset.id, dataset.filename)
		.then(function(dataResponse) {
		    getterService.getDatasets().then(function(dataResponse) {
			$scope.datasets = dataResponse['data'];
			$scope.successfullyUploaded=dataResponse['data'].length;
			getterService.broadcastDataset($scope.datasets);
		    }); // Update the datasets variable when deleting sth.
		    getterService.getStatistics().then(function(dataResponse) {
			$scope.statistics = dataResponse['data'];
		    }); // Populate the scope with the already computed statistics
		    
		});
	    if ($scope.showStatistics == dataset) {
		$scope.shownStatistics = null;
		$scope.showingStatistics = false;   
	    }
	}

	$scope.editDataset = function(dataset) {
	    $scope.editingDataset=true;
	    $scope.editedDataset=angular.copy(dataset);
	};

	$scope.cancelEdit = function(dataset) {
	    $scope.editedDataset = null;
	    $scope.editingDataset= false;
	};

	$scope.saveEdit = function(dataset) {
	    $scope.datasets  =_.map($scope.datasets, function(el) {
		return (el.id===dataset.id) ? dataset : el;
	    });
	    // Finish by sending the updated entry to the server
	    getterService.updateDataset(dataset.id, dataset)
		.then(getterService.broadcastDataset($scope.datasets));

	    $scope.cancelEdit(dataset); // End edition
	}

	//
	// ==== Logic of the statistics display
	//
	$scope.showDataset = function(dataset) {
	    $scope.shownStatistics = dataset;
	    $scope.showingStatistics = true;
	};
	
	//
	// ==== Upload (ng-flow) events
	//
	// (1) Fired when a file is added to the download list
	$scope.$on('flow::fileAdded', function (event, $flow, flowFile) {
	    $scope.currentlyUploading=true;
	});

	// (2) Fired when all downloads are complete
	$scope.$on('flow::complete', function (event, $flow, flowFile) {
	    $scope.currentlyUploading=false;
	});

	// (3) Fired when one download completes
	$scope.$on('flow::fileSuccess', function (file, message, chunk) {
	    getterService.getDatasets().then(function(dataResponse) {
		$scope.datasets = dataResponse['data'];
		$scope.successfullyUploaded=dataResponse['data'].length;
		$scope.poolPreprocessing = true; // start the watcher.
		getterService.broadcastDataset($scope.datasets);
	    });
	    getterService.getStatistics().then(function(dataResponse) {
		$scope.statistics = dataResponse['data'];
	    }); // Populate the scope with the already computed statistics
	});

	//
	// ==== Server-side processing after the upload
	//
	$scope.preprocessingStartStop = function() {
	    // A DEBUG function
	    $scope.poolPreprocessing = !$scope.poolPreprocessing;
	}
	preprocessingWaiter = $interval(function() {
	    // This loops forever, but might become inactive
	    if ($scope.poolPreprocessing) {
		getterService.getPreprocessing().then(function(dataResponse) {
		    getterService.getDatasets().then(function(dataResp) {
			$scope.datasets = dataResp['data'];
			$scope.successfullyUploaded=dataResp['data'].length;
			if (_.every(dataResponse['data'], function(el) {return el.state==='ok'})) {
			    getterService.broadcastDataset($scope.datasets);
			    $scope.poolPreprocessing = false;
			}
			
		    }); // Populate the scope with the already uploaded datasets
		    getterService.getStatistics().then(function(dataResponse) {
			$scope.statistics = dataResponse['data'];
		    }); // Populate the scope with the already computed statistics
		    // Check if all the dataset is "ok", if yes, switch the flag
		    if (_.every(dataResponse['data'], function(el) {return el.state==='ok'})) {
			//getterService.broadcastDataset($scope.datasets);
			$scope.poolPreprocessing = false;
		    }
		});
	    }
	    return(true)
	}, 2000);
    }]);
