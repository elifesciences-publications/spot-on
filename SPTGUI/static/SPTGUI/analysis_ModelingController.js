angular.module('app')
    .controller('ModelingController', ['analysisService', 'getterService', 'downloadService', 'ProcessingQueue', '$scope', '$rootScope', '$interval', '$q', function(analysisService, getterService, downloadService, ProcessingQueue, $scope, $rootScope, $interval, $q) {
	// This is the controller for the modeling tab
	$scope.downloads = []
	socketReady = false // not to double initialize after lost connexion
	$scope.$on('socket:ready', function() {
	    if (!socketReady) {
		console.log("Getting the list of downloads")
		downloadService.getDownloads()
		socketReady = true;
	    }
	})

	// When the socket is ready, initialize the downloads

	// Scope variables
	$scope.analysisState = 'notrun';
	$scope.computedJLD = 0
	$scope.showModelingTab = false;
	$scope.jldParsInit = false; // To avoid initializing twice

	initView = function() {
	    // Initiate the window with what we have
	    $scope.datasets = $scope.datasets.map(function(el) {
		el.incl=true; return el})

	    // Toggle buttons
	    initToggle = function(el) {
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
		}
	    };
	    $scope.datasetsToggle = $scope.datasets.map(initToggle)
	    $scope.datasetsToggleAll = function(val) {
		// Select all/none
		$scope.datasetsToggle.forEach(function(el){el(val)})
	    }
	    $scope.getNumberFittedDatasets = function() {
		// Returns the number of fitted datasets
		n = $scope.jlfit.filter(function(el){if (el) {return true}
						     else {return false}}).length
		if ($scope.jlpfit) {return n+1}
		else {return n}
	    }
	    $scope.numberComputedJLD = 0
	    getNumberComputedJLD = function(resp) {
		// Returns the number of computed datasets
		if (resp==='OK') {
		    $scope.numberComputedJLD++
		}
	    }
	    $scope.datasetsToggleAll(true);
	    
	    // Get the jump length distributions
	    // Should go through the pooled queue
	    // Then GET the jld
	    $scope.jlhist = $scope.datasets.map(function(el){return null;})
	    $scope.datasets.forEach(function(el, i) {
		if (el.jld_available) {
		    analysisService.getDefaultJLD(el.id).then(function(resp) {
			if (resp.data.status == 'done') {
			    $scope.jlhist[i] = resp.data.jld
			    $scope.showModelingTab = true;
			    $scope.analysisState = 'done';
			    console.log("Retrieved default JLD #"+el.id)
			}
		    })
		} else {
		    console.log("No JLD available for this dataset, weird")
		}
	    });
	    $scope.displayJLP(true)

	    $scope.jlfit = $scope.datasets.map(function(ll) {return null;}); // init fit
	}

	// When the datasets object has been loaded, it is stored there
	$scope.$on('datasets:loaded', function(event, datasets) {
	    $scope.datasets = datasets;
	    initView();
	});

	// When some datasets have been added to the list, we find the indices
	// of the old one and create blank slots for the new one
	$scope.$on('datasets:added', function(event, newDatasets) {
	    oldDatasets = angular.copy($scope.datasets)
	    oldIds = oldDatasets.map(function(el){return el.id})
	    
	    ids = newDatasets.map(function(el) {return el.id})
	    newids = ids.map(function(da_id, newId){
		oldid = oldIds.indexOf(da_id)
		if (oldid<0) {return null}
		else {return oldid}
	    })

	    // Update arrays
	    NdatasetsToggle = newids.map(function(el,i){
		if (el!==null) {return $scope.datasetsToggle[el]}
		else {return initToggle(newDatasets[i])}
	    })
	    $scope.datasetsToggle = NdatasetsToggle
	    
	    Njlhist = newids.map(function(el){
		if (el!==null) {return $scope.jlhist[el]}})
	    $scope.jlhist = Njlhist

	    Njlfit = newids.map(function(el){
		if (el!==null) {return $scope.jlfit[el]}})
	    $scope.jlfit = Njlfit
	    
	    // Download the jump length distributions of the new values
	    newDatasets.forEach(function(el, i) {
		if (!newids[i]) {
		    var myint = $interval(function() {
			analysisService.getDefaultJLD(el.id).then(function(resp) {
			    if (resp.data.status=='done') {
				$interval.cancel(myint)
				$scope.jlhist[i] = resp.data.jld
				$scope.showModelingTab = true;
				$scope.analysisState = 'done';
				console.log("Retrieved default JLD #"+el.id)
			    } else {
				console.log('JLD #'+el.id+' is still computing')
			    }
			})
		    }, 2000)
		}
	    })

	    $scope.datasets = newDatasets
	    
	    // Reset the pooled values
	    $scope.jlpfit = null;
	    $scope.jlphist = null;   
	})

	$scope.$on('datasets:deleted', function(event, data) {
	    // Updates the following arrays when a dataset is deleted
	    // datasets, datasetsToggle, jlhist, jlfit
	    da_id = data.dataset_id;
	    $scope.datasets = $scope.datasets
		.filter(function(el,i){return i!=da_id})
	    $scope.datasetsToggle = $scope.datasetsToggle
		.filter(function(el,i){return i!=da_id})
	    $scope.jlhist = $scope.jlhist.filter(function(el,i){return i!=da_id})
	    $scope.jlfit = $scope.jlfit.filter(function(el,i){return i!=da_id})

	    // Reset the pooled values
	    $scope.jlpfit = null;
	    $scope.jlphist = null;
	    
	    newIncl = $scope.modelingParameters.include
		.filter(function(el){return el != data.database_id})
	    $scope.modelingParameters.include = newIncl
	    
	})

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
	    if (!pars.MaxJump>0) {return false;}
	    if (!pars.TimeGap>0) {return false;}
	    return isOk
	}
	
	$scope.resetjldParameters = function() {
	    $scope.jldParameters = angular.copy($scope.jldParametersDefault);
	}
	
	$scope.$watch('jldParameters', function(pars, oldpars) {
	    if (angular.equals(pars, oldpars)) {return}
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
		$scope.jlhist = $scope.jlhist.map(function(el){return null});
		$scope.numberComputedJLD = 0
		// Recompute jld with new parameters
		analysisService.setNonDefaultJLD(pars).then(function(resp1) {
		    if (resp1.data) {
			prom = []
			resp1.data.forEach(function(el) {
			    if (el.celery_id) {
				prom.push(ProcessingQueue.addToQueue(el.celery_id, 'jld', getNumberComputedJLD))
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
				     ModelFit: false, //false: PDF, true: CDF fit
				     SingleCellFit: false,
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
	    $scope.jlpfit = null;
	    $scope.fitAvailable = false;
	    $scope.jlfit = $scope.datasets.map(function(el){return null});
	    analysisService.runAnalysis($scope.jldParameters, parameters).then(function(resp) {
		if (resp.data) {
		    resp.data.forEach(function(el) {
			if (el.celery_id != 'none') {
			    ProcessingQueue.addToQueue(el.celery_id, 'fit').then(function(resp2) {
				console.log("Fit done for dataset: "+ el.database_id)
				
				if (el.database_id == 'pooled') {
				    analysisService.getPooledFitted(JLDPars, FitPars).then(function(l) {
					$scope.jlpfit = l.data;
					$scope.analysisState = 'done';
					$scope.showJLPf = true;
				    })
				} else {
				    analysisService.getFitted(el.database_id, JLDPars, FitPars).then(function(l) {
					idd = $scope.datasets.map(function(ell){return ell.id}).indexOf(el.database_id)
					$scope.jlfit[idd] = l.data
					$scope.fitAvailable = true;
					$scope.analysisState = 'done'; // Hide progress bar
					if ($scope.modelingParameters.include.length == 1) { // Update if we have only one cell in the pooled fit
					    $scope.jlpfit = l.data;
					    $scope.showJLPf = true;
					}
				    })
				}
			    })
			} else {
			    console.log("Direct download of fit:" +el.database_id)
			    if (el.database_id == 'pooled' & $scope.modelingParameters.include.length>1) {
				analysisService.getPooledFitted(JLDPars, FitPars).then(function(l) {
				    $scope.jlpfit = l.data;
				    $scope.analysisState = 'done';
				    $scope.showJLPf = true;
				})
			    } else if (el.database_id == 'pooled' & $scope.modelingParameters.include.length==1) {
				console.log('The pooled fit will be uploaded later')
			    } else {
				    analysisService
					.getFitted(el.database_id, JLDPars, FitPars).then(function(l) {
					    idd = $scope.datasets.map(function(ell){return ell.id}).indexOf(el.database_id)
			    		    $scope.jlfit[idd] = l.data
			    		    $scope.analysisState = 'done';
					    if ($scope.modelingParameters.include.length == 1) { // Update if we have only one cell in the pooled fit
						$scope.jlpfit = l.data;
						$scope.showJLPf = true;
					    } else {
						$scope.fitAvailable = true;
					    }
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
	    var d = new Date()
	    var date_fmt = d.getDate()+'-'+(d.getMonth()+1)+'-'+d.getFullYear()+' '+d.getHours()+":"+d.getMinutes()
	    dwnlPars = {svg : $('#mainHist').html(),
			cell : $scope.datasets[$scope.ce].id,
			jldParams : angular.copy($scope.jldParameters),
			fitParams : angular.copy($scope.modelingParameters),
			jld : angular.copy($scope.jlhist),
			jldp: angular.copy($scope.jlphist),
			fit : angular.copy($scope.jlfit),
			fitp: angular.copy($scope.jlpfit),
			description: $scope.downloadPopover.description,
			date: date_fmt}
	    downloadService.setDownload(dwnlPars);
	    $scope.downloadPopover.isOpen = false;
	}

	$scope.downloadPopover = {
	    isOpen: false,
	    templateUrl: 'myPopoverTemplate.html',
	    description: '',
	    open: function open() {
		$scope.downloadPopover.isOpen = true;
            }
	};
    }]);
