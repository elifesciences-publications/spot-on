angular.module('app')
    .controller('ModelingController', ['analysisService', 'getterService', 'downloadService', 'ProcessingQueue', '$scope', '$interval', '$q', function(analysisService, getterService, downloadService, ProcessingQueue, $scope, $interval, $q) {
	// This is the controller for the modeling tab

	// Scope variables
	$scope.analysisState = 'notrun';
	$scope.computedJLD = 0	
	$scope.showModelingTab = false;
	$scope.jldParsInit = false; // To avoid initializing twice

	initView = function() {
	    // Initiate the window with what we have
	    $scope.datasets = $scope.datasets.map(function(el) {
		el.incl=false; return el})

	    // Toggle buttons
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
			$scope.showJLPf
			$scope.jlphist = null; // reset the hist when include changes
			$scope.jlpfit = null; // and the fit
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

	    // Get the jump length distributions
	    // Should go through the pooled queue
	    // Then GET the jld
	    $scope.jlhist = $scope.datasets.map(function(el){return null;})
	    $scope.datasets.forEach(function(el, i) {
		if (el.jld_available) {
		    analysisService.getDefaultJLD(el.id).then(function(resp) {
			$scope.jlhist[i] = resp.data
			$scope.showModelingTab = true; // Hide progress bar
			$scope.analysisState = 'done';
			console.log("Retrieved default JLD for dataset "+el.id)
		    })
		} else {
		    console.log("No JLD available for this dataset, weird")
		}
	    });

	    $scope.jlfit = $scope.datasets.map(function(ll) {return null;}); // init fit
	}

	// When the datasets object has been loaded, it is stored there
	$scope.$on('datasets:loaded', function(event, datasets) {
	    $scope.datasets = datasets;
	    initView();
	});

	$scope.$on('datasets:updated', function(event,data) {
	    console.load("updated dataset Modeling controller. DEPRECATED")
	    $scope.datasets = data
	    
	    // Now reset everything
	    $scope.jlphist = null;
	    $scope.jlpfit = null;
	    $scope.ce = 0;
	    $scope.dt = 1;
	    $scope.showJLP = false;
	    $scope.showJLPf = false;
	    $scope.modelingParameters.include = [];
	    $scope.jlhist = null;
	    $scope.jlfit = $scope.datasets.map(function(el){return null;})
	    $scope.analysisState = 'notrun';

	    initView(); // And initialize stuff again
	});
	
	//
	// ==== CRUD modeling parameters
	//
	$scope.jldParameters = {BinWidth : 0.01,
				GapsAllowed : 1,
				TimePoints : 8,
				JumpsToConsider : 4,
				MaxJump : 1.25,
				TimeGap : 4.477}
	$scope.jldParametersDefault = angular.copy($scope.jldParameters);
	
	validateJLDparameters = function(pars) {
	    isOk = true
	    if (!pars.BinWidth>0) {return false;}
	    if (!pars.GapsAllowed>=1) {return false;}
	    if (!pars.JumpsToConsider>=3) {return false;}
	    return isOk
	}
	
	$scope.resetjldParameters = function() {
	    $scope.jldParameters = angular.copy($scope.jldParametersDefault);
	}
	
	$scope.$watch('jldParameters', function(pars) {
	    // Reset the variables
	    if (!$scope.jldParsInit) {
		$scope.jldParsInit = true
		return
	    }
	    $scope.jlfit = $scope.datasets.map(function(el){return null;});
	    $scope.jlpfit = null;
	    $scope.jlphist = null;
	    $scope.probingJLD = true;
	    $scope.analysisState = 'jld'; // Hide plot

	    // Check that the inputs are ok
	    if (!validateJLDparameters(pars)) {
		alert("Parameters are not good")
	    } else {
		// Recompute jld with new parameters
		incrementJLD = function(resp) {
		    if (resp == 'OK') {
			$scope.computedJLD = $scope.computedJLD+1;
		    }
		}
		$scope.computedJLD = 0;
		analysisService.setNonDefaultJLD(pars).then(function(resp1) {
		    if (resp1.data) {
			prom = []
			resp1.data.forEach(function(el) {
			    if (el.celery_id) {
				prom.push(ProcessingQueue.addToQueue(el.celery_id, 'jld', incrementJLD))
			    }
			})
			$q.all(prom).then(function(arr) {
			    analysisService.getNonDefaultJLD(pars)
				.then(function(resp2){
				    if (resp2.data.status == 'done') {
					$scope.computedJLD = 0;
				    	$scope.jlhist = resp2.data.jld;
				    	$scope.analysisState = 'done';
				    	$scope.probingJLD = false;
				    } else if (resp2.data.length==0) {
				    	$scope.probingJLD = false;
				    }
				})
			})
		    }
		})
	    }
	}, true); // deep watch the object
	
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
	$scope.jlpfit = null; // Pooled fit
	$scope.showJLP = false;
	$scope.showJLPf = false;
	
	//
	// ==== Analysis computation logic
	//

	// Function that runs the analysis
	$scope.runAnalysis = function(parameters) {
	    if (parameters.include.length == 0){
		alert('no dataset included! Make a selection');
		return;
	    }
	    analysisService.runAnalysis($scope.jldParameters, parameters).then(function(resp) {
		if (resp.data) {
		    resp.data.forEach(function(el) {
			if (el.celery_id != 'none') {
			    ProcessingQueue.addToQueue(el.celery_id, 'fit').then(function(resp2) {
				console.log("Fit done for dataset: "+ el.database_id)
				if (el.database_id == 'pooled') {
				    analysisService.getPooledFitted(JLDPars, FitPars).then(function(l) {
					$scope.jlpfit = l.data;
				    })
				} else {
				    analysisService.getFitted(el.database_id, JLDPars, FitPars).then(function(l) {
					idd = $scope.datasets.map(function(ell){return ell.id}).indexOf(el.database_id)
					$scope.jlfit[idd] = l.data
					$scope.fitAvailable = true;
					$scope.analysisState = 'done'; // Hide progress bar
				    })
				}
			    })
			} else {
			    console.log("Direct download of fit:" +el.database_id)
			    if (el.database_id == 'pooled') {
				    analysisService.getPooledFitted(JLDPars, FitPars).then(function(l) {
					$scope.jlpfit = l.data;
				    })				
				} else {
				    analysisService
					.getFitted(el.database_id, JLDPars, FitPars).then(function(l) {
					    idd = $scope.datasets.map(function(ell){return ell.id}).indexOf(el.database_id)
			    		    $scope.jlfit[idd] = l.data
			    		    $scope.fitAvailable = true;
			    		    $scope.analysisState = 'done';
					})
				}
			}
		    })
		}
	    })
	    $scope.analysisState='running'; // 'running' for progress bar
	    $scope.fitAvailable = false;
	    FitPars = $scope.modelingParameters;
	    JLDPars = $scope.jldParameters;
	}
	
	// A watcher that periodically checks the state of the computation
	// processingWaiter = $interval(function() {
	//     // This loops forever, but might become inactive
	//     if ($scope.analysisState=='running') {
	// 	$scope.fitAvailable = false;
	// 	FitPars = $scope.modelingParameters;
	// 	JLDPars = $scope.jldParameters;
	// 	analysisService.checkAnalysis(JLDPars, FitPars)
	// 	    .then(function(dataResponse) {
	// 		if (dataResponse['data'].allgood) {
	// 		    analysisService.getPooledFitted(JLDPars, FitPars).then(
	// 			function(l) {
	// 			    $scope.jlpfit = l.data;
	// 			}
	// 		    );
	// 		    $q.all(FitPars.include.map(function(data_id) {
	// 			return analysisService.getFitted(data_id, JLDPars, FitPars);
	// 		    })).then(function(l) {
	// 			$scope.jlfit = l.map(function(ll){return ll.data});
	// 			$scope.fitAvailable = true;
	// 			$scope.analysisState = 'done'; // Hide progress bar
	// 		    });
	// 		}
	// 	    });
	//     }
	//     return(true)
	// }, 2000);
	
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
		    analysisService.getPooledJLD($scope.jldParameters, $scope.modelingParameters.include).then(
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

	// The logic behind the toggle switch to show the JLPf
	// The logic behind the toggle switch to show the JLP
	$scope.displayJLPf = function(newVal) {
	    if (arguments.length) {
		if (newVal == true) {
		    if (!$scope.jlpfit) {return;}
		    // Check that we have everything we need to display
		    else {$scope.showJLPf = true;}
		}
		else {$scope.showJLPf = false;}
	    }
	    else {return $scope.showJLPf;}
	}

	// The function to mark the current SVG view to download
	$scope.toDownloads = function() {
	    dwnlPars = {svg : $('#mainHist').html(),
			format : 'svg',
			cell : $scope.datasets[$scope.ce].id,
			jldParams : angular.copy($scope.jldParameters),
			fitParams : angular.copy($scope.modelingParameters),
			jld : angular.copy($scope.jlhist),
			jldp: angular.copy($scope.jlphist),
			fit : angular.copy($scope.jlfit),
			fitp: angular.copy($scope.jlpfit)}
	    downloadService.setDownload(dwnlPars);
	    alert("Analysis marked for download");
	}
    }]);
