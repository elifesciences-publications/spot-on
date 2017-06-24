angular.module('app')
    .controller('UploadController', ['getterService', 'MainSocket', 'ProcessingQueue', '$scope', '$cookies', '$interval', '$q', '$rootScope', function(getterService, MainSocket, ProcessingQueue, $scope, $cookies, $interval, $q, $rootScope) {
	// This is the controller for the upload part of the app

	//
	// ==== Let's first define some global variables (on the $scope).
	//
	socketReady = false;
	$scope.datasetsReady = false;
	$scope.establishedConnexion=false;
	$scope.currentlyUploading=false;
	$scope.successfullyUploaded=0;
	$scope.editingDataset=false;
	$scope.editedDataset=null;
	$scope.showingStatistics=false;
	$scope.shownStatistics=null;
	$scope.statistics = null;
	$scope.uploadFormat = {format: null, params: null, currentParams: null};

	//
	// ==== Initializing the view
	//
	$scope.uploadStart = function($flow){ //Populate $flow with the CSRF cookie
	    $flow.opts.headers =  {'X-CSRFToken' : $cookies.get("csrftoken")};
	};

	//
	// ==== Get basic information. We need to wait for the socket to be
	//      initiated for that.
	//
	$scope.$on('socket:ready', function() {
	    if (!socketReady) {
		p1 = getterService.getDatasets2() // Retrieve existing datasets
		p2 = getterService.getGlobalStatistics() // Get global statistics
		$scope.establishedConnexion=true;
		socketReady = true; // avoid doing that again when conn. lost
		
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
		    $rootScope.$broadcast('datasets:statistics', $scope.statistics);
		    $scope.datasetsReady = true;
		})

		// Retrieve available file formats
		getterService.getFileFormats().then(function success(resp) {
		    $scope.acceptedFormats = resp;
		}, function error(resp) {
		    alert('could not retrieve the list of available file formats')
		})
	    }
	});

	//
	// ==== CRUD: handle format selection
	//
	$scope.setFormat = function(format) {
	    $scope.uploadFormat.params = format;
	    $scope.uploadFormat.currentParams = {};
	    format[1].params.forEach(function(el) {
		$scope.uploadFormat.currentParams[el.model] = null;
	    })
	}

	// Function to determine whether the Upload Drag'n'drop box should be
	//+displayed. We only display it when all the parameters required for the
	//+selected format have been filled in, because these are directly sent to
	//+the server.
	$scope.showUploadZone = function() {
	    curPars = $scope.uploadFormat.currentParams; // shortcut name
	    if ($scope.uploadFormat.format!==null & curPars !== null) {
		out = true
		for (var property in curPars) {
		    if (curPars.hasOwnProperty(property)) {
			if (curPars[property]===null) { out = false }
		    }
		}
		return out
	    }
	    return false
	}
	//
	// ==== CRUD: Handle the edition of the list of files
	//
	$scope.deleteDataset = function(dataset, idx) {
	    dataset = angular.copy(dataset)
	    $scope.datasets.splice(idx,1)
	    $scope.successfullyUploaded=$scope.successfullyUploaded-1;
	    
	    getterService.deleteDataset(dataset.id, dataset.filename)
		.then(function(dataResponse) {
		    da_id = dataset.id
		    getterService.broadcastDeletedDataset(da_id, idx,
							  $scope.datasets);

		    // Upload the global statistics
		    // TODO: hide the statistics while uploading
		    $scope.statistics = null;
		    getterService.getGlobalStatistics().then(function(resp) {
			$scope.statistics = resp;
			$rootScope.$broadcast('datasets:statistics', $scope.statistics);
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
		.then(getterService.broadcastEditedDataset(dataset.id, dataset));
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
	// ==== Logic of the validation of statistics
	// Validation of the statistics
	var nada = {classe:'', pict: false, msg: ""}
	var errr = {classe:'alert alert-danger',
		    pict: true,
		    msg: ""}
	$scope.validate = {
	    dt2: function() {
		if (!$scope.datasets) {return false};
		d0 = $scope.datasets[0];
		return !$scope.datasets.every(function(el) {return el.dt==d0.dt;})
	    },
	    dt: function(data) {
		if (data>0.01) {
		    errr.msg = "The framerate is less than 10 Hz"
		    return errr
		} else {return nada}
	    },
	    ntraces: function(data) {
		if (data<100) {
		    errr.msg = "This dataset contains <100 traces"
		    return errr
		} else {return nada}
	    },
	    nframes: function(data) {
		if (data<100) {
		    errr.msg = "This dataset contains <100 frames"
		    return errr
		} else {return nada}
	    },
	    npoints: function(data) {
		if (data<1000) {
		    errr.msg = "This dataset contains <1000 detections"
		    return errr
		} else {return nada}
	    },
	    ngaps: function(data) {
		if (data>2) {
		    errr.msg = "This dataset contains gaps of more than 2 frames"
		    return errr
		} else {return nada}
	    },
	    ntraces3: function(data) {
		if (data<100) {
		    errr.msg = "This dataset contains <100 traces of >= 3 detections."
		    return errr
		} else {return nada}
	    },
	    njumps: function(data) {
		if (data<1000) {
		    errr.msg = "This dataset contains <1000 jumps"
		    return errr
		} else {return nada}
	    },
 	    median_length_of_trajectories: function(data) {
		if (data<=2) {
		    errr.msg = ">50% of the trajectories last two frames or less."
		    return errr
		} else {return nada}
	    },
 	    median_particles_per_frame: function(data) {
		if (data>1) {
		    errr.msg = ">50% of the frames contain more than one detection."
		    return errr
		} else {return nada}
	    },
 	    median_jump_length: function(data) {
		if (data>1) {
		    errr.msg = ">50% of the jumps are more than 1 µm."
		    return errr
		} else {return nada}
	    }
	}
	
	
	//
	// ==== Upload (ng-flow) events
	//
	// (1) Fired when a file is added to the download list
	$scope.$on('flow::fileAdded', function (event, $flow, flowFile) {
	    $flow.opts.query = { parserName: $scope.uploadFormat.params[0], 
				 parserParams: JSON.stringify($scope.uploadFormat.currentParams) }; // Send file type info
	    $scope.currentlyUploading=true;
	});

	// (2) Fired when all downloads are complete
	$scope.$on('flow::complete', function (event, $flow, flowFile) {
	    getterService.getGlobalStatistics().then(function(resp) {
		$scope.statistics = resp;
		$rootScope.$broadcast('datasets:statistics', $scope.statistics);
	    });
	});

	// (3) Fired when testing if the download is complete, until the
	// last dataset has been processed
	currentlyUploadingPrevious = false
	$interval(function() {
	    if ($scope.currentlyUploading||currentlyUploadingPrevious) {
		getterService.getDatasets2().then(function(resp) {
		    le = $scope.datasets.length
		    $scope.datasets = resp;
		    $scope.successfullyUploaded=resp.length;
		    if (le<resp.length) {
			getterService.broadcastAddedDatasets($scope.datasets);
		    }
		});
	    }
	    if ($scope.currentlyUploading != currentlyUploadingPrevious) {
		if (currentlyUploadingPrevious) {
		    console.log("Getting global statistics")
		    getterService.getGlobalStatistics().then(function(resp) {
			$scope.statistics = resp;
			$rootScope.$broadcast('datasets:statistics', $scope.statistics);
		    });
		}
		currentlyUploadingPrevious = $scope.currentlyUploading
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
			    $scope.currentlyUploading=false;
			})
		    $interval.cancel(checkExist);
		    message.cancel();		    
		}
	    }, 100);	    
	});
    }]);
