angular.module('app')
    .controller('ModelingController', ['analysisService', 'getterService', '$scope', '$interval', '$q', function(analysisService, getterService, $scope, $interval, $q) {
	// This is the controller for the modeling tab

	// Scope variables
	$scope.analysisState = 'notrun';

	// Initiate the window with what we have
	getterService.getDatasets().then(function(dataResponse) {
	    $scope.datasets = dataResponse['data'];
	    $scope.datasets = $scope.datasets.map(function(el) {
		el.incl=false; return el})
	    $scope.datasetsf = $scope.datasets.map(function(el) {
		return function(newVal) {
		    function add(array, value) {
			if (array.indexOf(value) === -1) {array.push(value);}
		    }

		    function remove(array, value) {
			var index = array.indexOf(value);
			if (index !== -1) {array.splice(index, 1);}
		    }
		    
		    if (arguments.length) {
			$scope.showJLP = false; // plot-related
			$scope.jlphist = null; // reset the hist when include changes
			if (newVal == true) {
			    add($scope.modelingParameters.include, el.id)
			} else {
			    remove($scope.modelingParameters.include, el.id)
			}
			el.incl = newVal
		    } else {
			return el.incl
		    }
		}});
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
				     include : [] // Populated later
				    };
	$scope.dt = 1; // Display parameter
	$scope.ce = 0;
	$scope.fitAvailable = false;
	$scope.gettingPooledJLD = false;
	$scope.jlphist = null; // Pooled JLD
	$scope.showJLP = false;

	//
	// ==== Analysis computation logic
	//

	// Function that runs the analysis
	$scope.runAnalysis = function(parameters) {
	    // Show a progress bar (synced from messages from the broker)
	    // $scope.$applyAsync();
	    if (parameters.include.length == 0){
		alert('no dataset included! Make a selection');
		return;
	    }
	    analysisService.runAnalysis(parameters)   
	    $scope.analysisState='running'; // 'running' for progress bar
	}

	// Function that does everything to display a pooled jld
	$scope.getPooledJLD = function() {
	    if (!$scope.modelingParameters.include||$scope.modelingParameters.include.length==0)
	    {
		alert('no dataset selected');
		return;
	    }
	    
	    $scope.gettingPooledJLD = true;
	    $interval(function() {
		if ($scope.gettingPooledJLD) {
		    analysisService.getPooledJLD($scope.modelingParameters).then(
			function(l) {
			    if (l.data != 'computing') {
				$scope.jlphist = l.data
				$scope.gettingPooledJLD = false; // plot-related
				$scope.showJLP = true; // plot-related
				return false;
			    }
			});
		}
		return true;}, 500);
	}

	// The logic behind the toggle switch to show the JLP
	$scope.displayJLP = function(newVal) {
	    if (arguments.length) {
		if (newVal == true) {
		    if (!$scope.jlphist) {
			$scope.getPooledJLD();
		    }
		    // Check that we have everything we need to display
		    else if (!$scope.modelingParameters.include||$scope.modelingParameters.include.length==0)
		    {
			$scope.showJLP = false;
		    }
		    else {
			$scope.showJLP = true;}
		} else {
		    $scope.showJLP = false;
		}
	    } else {
		return $scope.showJLP;
	    }
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
