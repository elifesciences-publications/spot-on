angular.module('app')
    .controller('UploadController', ['getterService', 'MainSocket', 'ProcessingQueue', '$scope', '$cookies', '$interval', '$q', function(getterService, MainSocket, ProcessingQueue, $scope, $cookies, $interval, $q) {
	// This is the controller for the upload part of the app

	//
	// ==== Let's first define some global variables (on the $scope).
	//
	$scope.establishedConnexion=false;
	$scope.currentlyUploading=false;
	$scope.successfullyUploaded=0;
	$scope.editingDataset=false;
	$scope.editedDataset=null;
	$scope.showingStatistics=false;
	$scope.shownStatistics=null;
	$scope.statistics = null;

	//
	// ==== Initializing the view
	//
	$scope.uploadStart = function($flow){
	    $flow.opts.headers =  {'X-CSRFToken' : $cookies.get("csrftoken")};
	}; // Populate $flow with the CSRF cookie!


	//
	// ==== Get basic information. We need to wait for the socket to be
	//      initiated for that.
	//
	$scope.$on('socket:ready', function () {
	    p1 = getterService.getDatasets2() // Retrieve existing datasets
	    p2 = getterService.getGlobalStatistics() // Retrieve global statistics

	    $q.all([p1,p2]).then(function(o){
		// Update datasets
		r1 = o[0]
		$scope.datasets = r1;
		$scope.successfullyUploaded=r1.length;

		// Update statistics
		r2 = o[1]
		$scope.statistics = r2;

		// Be done!
		getterService.broadcastLoadedDatasets($scope.datasets)
		$scope.establishedConnexion=true;
	    })
	});

	//
	// ==== CRUD: Handle the edition of the list of files
	//
	$scope.deleteDataset = function(dataset, idx) {
	    getterService.deleteDataset(dataset.id, dataset.filename)
		.then(function(dataResponse) {
		    da_id = dataset.id
		    $scope.datasets.splice(idx,1)
		    getterService.broadcastDeletedDataset(da_id, idx);
		    $scope.successfullyUploaded=$scope.successfullyUploaded-1;

		    // Upload the global statistics
		    // TODO: hide the statistics while uploading
		    getterService.getGlobalStatistics().then(function(resp) {
			$scope.statistics = resp;
		    });

		    console.log("Deleted dataset "+idx)
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
		.then(getterService.broadcastEditedDataset(dataset.id));
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
	    getterService.getGlobalStatistics().then(function(resp) {
		$scope.statistics = resp;
	    });
	    //$scope.currentlyUploading=false;
	});

	// (3) Fired when testing if the download is complete
	$interval(function() {
	    if ($scope.currentlyUploading) {
		getterService.getDatasets2().then(function(resp) {
		    $scope.datasets = resp;
		    $scope.successfullyUploaded=resp.length;
		    //getterService.broadcastAddedDataset(resp[resp.length-1], resp.length-1);
		});
	    }
	}, 2000)
	

	// (4) Fired when one download completes
	$scope.$on('flow::fileSuccess', function (file, message, chunk) {
	    if (message.file) {resp = message.file}
	    else if (message.files) {resp = message.files[message.files.length-1]}
	    else {console.log('not getting the right object')}
	    var checkExist = $interval(function() {
		if (resp.msg) {
		    celery_id = JSON.parse(resp.msg).celery_id;
		    celid = celery_id[0]+'@'+celery_id[1]
		    ProcessingQueue.addToQueue(celid, 'preprocessing')
			.then(function(res){
			    console.log(res)
			    getterService.getDatasets2().then(function(resp) {
				$scope.datasets = resp;
				$scope.successfullyUploaded=resp.length;
				getterService.broadcastAddedDataset(resp[resp.length-1], resp.length-1);
			    });
			})
		    $interval.cancel(checkExist);
		    message.cancel();		    
		}
	    }, 100);	    
	});
    }]);
