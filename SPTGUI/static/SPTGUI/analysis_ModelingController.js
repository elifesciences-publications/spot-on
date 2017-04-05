angular.module('app')
    .controller('ModelingController', ['analysisService', 'getterService', '$scope', '$interval', '$q', function(analysisService, getterService, $scope, $interval, $q) {
	// This is the controller for the modeling tab

	// Scope variables
	$scope.analysisState = 'notrun';

	// Initiate the window with what we have
	getterService.getDatasets().then(function(dataResponse) {
	    $scope.datasets = dataResponse['data'];
	    $q.all($scope.datasets.map(function(el) { // Get JLD when available
		if (el.jld_available) {
		    return getterService.getJLD(el.id);
		}
		else {return null;}
	    })).then(function(l) {
		$scope.jlhist = l.map(function(ll){
		    if (!ll) {return null;}
		    return ll.data
		});
		$scope.jlfit = l.map(function(ll) {return null;}); // init fit
		$scope.analysisState = 'done'; // Hide progress bar
	    });		    
	}); // Populate the scope with the already uploaded datasets
	getterService.getStatistics().then(function(dataResponse) {
	    $scope.statistics = dataResponse['data'];
	}); // Populate the scope with the already computed statistics
	$scope.$on('datasets:updated', function(event,data) {
	    $scope.datasets = data
	}); // Look for updated datasets
	
	//
	// ==== CRUD modeling parameters
	//

	$scope.modelingParameters = {D_free : [0.15, 25],
				     D_bound: [0.0005, 0.08],
				     F_bound: [0, 1],
				     LocError: 0.035,
				     iterations: 3,
				     dT: 4.477/1000,
				     dZ: 0.700,
				     ModelFit: 1, //1: PDF fit, 2: CDF fit
				     include : null // Populated later
				    };
	$scope.dt = 1; // Display parameter
	$scope.ce = 0;
	$scope.fitAvailable = false;

	//
	// ==== Analysis computation logic
	//

	// Function that runs the analysis
	$scope.runAnalysis = function(parameters) {
	    // Show a progress bar (synced from messages from the broker)
	    $scope.modelingParameters.include = $scope.datasets.map(function(l){return l.id;})
	    // $scope.$applyAsync();
	    analysisService.runAnalysis(parameters)   
	    $scope.analysisState='running'; // 'running' for progress bar
	}

	// A watcher that periodically checks the state of the computation
	processingWaiter = $interval(function() {
	    // This loops forever, but might become inactive
	    if ($scope.analysisState=='running') {
		$scope.fitAvailable = false;
		pars = $scope.modelingParameters;
		analysisService.checkAnalysis(pars)
		    .then(function(dataResponse) {
			if (dataResponse['data'].allgood) {
			    $q.all(pars.include.map(function(data_id) {
				return analysisService.getFitted(data_id, pars);
			    })).then(function(l) {
				$scope.jlfit = l.map(function(ll){return ll.data});
				$scope.fitAvailable = true;
				$scope.analysisState = 'done'; // Hide progress bar
			    });
			}
		    });
	    }
	    return(true)
	}, 2000);
    }]);
