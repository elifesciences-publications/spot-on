angular.module('app')
    .controller('ModelingController', ['analysisService', 'getterService', 'downloadService', 'ProcessingQueue', '$scope', '$rootScope', '$interval', '$q', '$timeout', function(analysisService, getterService, downloadService, ProcessingQueue, $scope, $rootScope, $interval, $q, $timeout) {
	// This is the controller for the modeling tab

	// Get the list of the analyses saved for download.
	$scope.downloads = []
	$scope.$on('downloads:updated', function(downloads) {
	    $scope.downloads = downloads;
	})
	    

	// When the socket is ready, initialize the downloads

	// Scope variables
	$scope.analysisState = 'notrun';
	$scope.computedJLD = 0
	$scope.showModelingTab = false;
	$scope.jldParsInit = false; // To avoid initializing twice
	$scope.fitComplete = true;
	$scope.displayCDF = false; // Commanded by toggle switch
	$scope.zcorr = {a: null, b: null}
	
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
			//$scope.showJLPf
			$scope.jlphist = null; // reset the hist when include changes
			$scope.jlpfit = null; // and the fit
			$scope.showJLPf = false;
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
	    $scope.getNumberDatasetsToFit = function() {
		if ($scope.modelingParameters.SingleCellFit) {
		    return $scope.modelingParameters.include.length+1;
		} else {
		    return 1; // Only fit the pooled distribution
		}
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
			    $scope.showModelingTab = true;
			    $scope.analysisState = 'done';
			    refreshMaxJumpSlider();
			    $scope.jlhist[i] = resp.data.jld
			    console.log("Retrieved default JLD #"+el.id)
			    $scope.$broadcast('datasets:redraw', $scope.datasets);
			}
		    })
		} else {
		    console.log("No JLD available for this dataset, weird")
		}
	    });
	    if ($scope.modelingParameters.include.length>0) {
		$scope.displayJLP(true)
	    }

	    $scope.jlfit = $scope.datasets.map(function(ll) {return null;}); // init fit
	}
	$scope.initView = initView // debug

	// When the datasets object has been loaded, it is stored there
	$scope.$on('datasets:loaded', function(event, datasets) {
	    $scope.datasets = datasets;
	    initView();
	});
	// Name/description of the datasets have been updated
	$scope.$on('dataset:updated', function(event, dataset_id, dataset) {
	    $scope.datasets = $scope.datasets.map(function(el) {
		return el.id==dataset_id ? dataset : el
	    })
	    console.log("updated dataset "+dataset_id);
	});

	// Get the number of gaps when statistics are computed.
	$scope.$on('datasets:statistics', function(event, statistics) {
	    if (statistics.hasOwnProperty('pre_ngaps')) {
		$scope.jldParameters.GapsAllowed = parseFloat(statistics.pre_ngaps)
	    }
	})

	// When some datasets have been added to the list, we find the indices
	// of the old one and create blank slots for the new one
	$scope.$on('datasets:added', function(event, newDatasets) {
	    oldDatasets = angular.copy($scope.datasets)
	    oldIds = oldDatasets.map(function(el){return el.id})

	    // Hide the plot
	    $scope.displayJLP(false)
	    
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
				$scope.showModelingTab = true;
				$scope.analysisState = 'done';
				refreshMaxJumpSlider();
				$scope.jlhist[i] = resp.data.jld
				console.log("Retrieved default JLD #"+el.id)
				//$scope.$broadcast('datasets:redraw', $scope.datasets);
			    } else {
				console.log('JLD #'+el.id+' is still computing')
			    }
			})
		    }, 2000)
		}
	    })

	    $scope.datasets = newDatasets
	    
	    // Reset the pooled values
	    $scope.showJLPf = false
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
	    $scope.displayJLP(false)
	    $scope.showJLPf = false;
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
				useAllTraj: false,
				GapsAllowed : 0,
				TimePoints : 8,
				JumpsToConsider : 4,
				MaxJump : 3,
				TimeGap : 4.477}
	$scope.jldParametersDefault = angular.copy($scope.jldParameters);
	$scope.maxJumpSlider = { value: 1.2,
				 options: { floor: 0,
					    ceil: $scope.jldParameters.MaxJump,
					    step: 0.1,
					    precision: 1}
			       };

	validateJLDparameters = function(pars) {
	    isOk = true
	    if (!(pars.BinWidth>0)) {return false;}
	    if (!(pars.GapsAllowed>=0)) {return false;}
	    if (!(pars.JumpsToConsider>=3)) {return false;}
	    if (!(pars.MaxJump>0)) {return false;}
	    if (!(pars.TimeGap>0)) {return false;}
	    if (pars.useAllTraj) {
		pars.JumpsToConsider = $scope.jldParametersDefault.JumpsToConsider
	    }
	    if (pars.MaxJump/pars.BinWidth>2500) {
		alert("There should not be more than 2500 bins, ie. Max Jump/Bin Width < 2500. Eaither increase the Bin Width or decrease the Max Jump.")
		return false
	    }
	    return isOk
	}

	$scope.showComputeJLDbutton =  function() {
	    return ($scope.jlhist.length>=5)
	}
	
	$scope.resetjldParameters = function() {
	    $scope.jldParameters = angular.copy($scope.jldParametersDefault);
	}
	
	$scope.$watch('jldParameters', function(pars, oldpars) {
	    if (angular.equals(pars, oldpars)) {return}
	    // Update MaxJump slider
	    $scope.maxJumpSlider.options.ceil = pars.MaxJump;
	    // Update dT of modelingParameters
	    $scope.modelingParameters.dT = pars.TimeGap/1000.;
	    // Reset the variables
	    $scope.jlfit = $scope.datasets.map(function(el){return null;});
	    $scope.showJLPf = false;
	    $scope.displayJLP(false);
	    $scope.jlpfit = null;
	    $scope.jlphist = null;
	    $scope.probingJLD = true;
	    // Check that the inputs are ok
	    if (!validateJLDparameters(pars)) {
		alert("Parameters are not good")
	    } else if ($scope.showComputeJLDbutton()) {
		$scope.analysisState = 'jld_notrun'; // Hide plot
	    } else {
		runJLD(pars)
	    }
	}, true); // deep watch the object
	
	$scope.modelingParameters = {D_free : [0.15, 25],
				     D_fast : [0.15, 25],
				     D_med : [0.15, 5], // D_slow
				     D_bound: [0.0005, 0.08],
				     F_bound: [0, 1],
				     F_fast:  [0, 1],
				     sigma: [0.01, 0.1],
				     LocError: 0.035,
				     iterations: 3,
				     dT: 4.477/1000,
				     dZ: 0.700,
				     ModelFit: false, //false: PDF, true: CDF fit
				     fitSigma: false,
				     SingleCellFit: false,
				     include : [], // Populated later
				     fit2states : null,
				    };
	modelingParametersDefault = angular.copy($scope.modelingParameters)
	$scope.ce = 1;
	$scope.fitAvailable = null;
	$scope.gettingPooled
	$scope.showJLP = false;
	$scope.showJLPf = false;
	$scope.jlphist = null; // Pooled JLD
	$scope.jlpfit = null; // Pooled fit
	
	//
	// ==== Analysis computation logic
	//

	// Function that computes the JLD
	runJLD = function(pars) {
	    $scope.analysisState = 'jld'; // Hide plot
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
				    refreshMaxJumpSlider();
				    $scope.probingJLD = false;
				} else if (resp2.data.length==0) {
				    $scope.probingJLD = false;
				}
			    })
		    })
		}
	    })
	}
	$scope.runJLD = runJLD

	// Function that runs the analysis
	$scope.runAnalysis = function(parameters) {
	    if (parameters.include.length == 0){
		alert('no dataset included! Make a selection');
		return;
	    }
	    if (parameters.fit2states === null) {
		alert('No kinetic model selected! Make a selection, either two states or three states.');
		return;
	    }
	    $scope.fitComplete = false;
	    $scope.showJLPf = false;
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
					refreshMaxJumpSlider();
					$scope.showJLPf = true;
					$scope.fitAvailable = true;
					$scope.displayJLP(true)
				    })
				} else {
				    analysisService.getFitted(el.database_id, JLDPars, FitPars).then(function(l) {
					idd = $scope.datasets.map(function(ell){return ell.id}).indexOf(el.database_id)
					$scope.jlfit[idd] = l.data
					$scope.fitAvailable = true;
					$scope.analysisState = 'done'; // Hide progress bar
					refreshMaxJumpSlider();
					if ($scope.modelingParameters.include.length == 1) { // Update if we have only one cell in the pooled fit
					    $scope.jlpfit = l.data;
					    $scope.showJLPf = true;
					    $scope.fitAvailable = false
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
				    refreshMaxJumpSlider();
				    $scope.showJLPf = true;
				    $scope.fitAvailable = false
				})
			    } else if (el.database_id == 'pooled' & $scope.modelingParameters.include.length==1) {
				console.log('The pooled fit will be uploaded later')
			    } else {
				    analysisService
					.getFitted(el.database_id, JLDPars, FitPars).then(function(l) {
					    idd = $scope.datasets.map(function(ell){return ell.id}).indexOf(el.database_id)
			    		    $scope.jlfit[idd] = l.data
			    		    $scope.analysisState = 'done';
					    refreshMaxJumpSlider();
					    $scope.fitAvailable = false
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

	// The logic behind the "fit localization error" switch
	$scope.fitLocalizationError = function() {
	    if ($scope.modelingParameters.fitSigma) {
		$scope.modelingParameters.LocError = null;
		$scope.modelingParameters.sigma = modelingParametersDefault.sigma;
	    } else {
		$scope.modelingParameters.sigma = null
		$scope.modelingParameters.LocError = angular.copy(modelingParametersDefault.LocError);
	    }
	}
	
	// The logic behind the switch between the two and three states model
	$scope.init2states = function(nstates) {
	    if (nstates==2) {
		$scope.modelingParameters.D_free = modelingParametersDefault.D_free
		delete $scope.modelingParameters.D_fast
		delete $scope.modelingParameters.D_med
		delete $scope.modelingParameters.F_fast
	    } else if (nstates==3) {
		delete $scope.modelingParameters.D_free
		$scope.modelingParameters.D_fast = modelingParametersDefault.D_fast
		$scope.modelingParameters.D_med = modelingParametersDefault.D_med
		$scope.modelingParameters.F_fast = modelingParametersDefault.F_fast
	    } else {
		console.log("unknown number of states")
		return
	    }
	    console.log("switching to a "+nstates+" states kinetic model")
	}

	// The function to get the ids of the selected datasets
	$scope.getSelectedIds = function() {
	    return $scope.modelingParameters.include.map(function(el) {
		idd = -1
		$scope.datasets.forEach(function(ell, i) {
		    if (ell.id == el) {idd = i}
		})
		return idd+1 // shift by one
	    })
	}

	// Returns if we should show the progress bar
	$scope.isFitting = function() {
	    if (($scope.fitAvailable === null)|($scope.fitComplete)){return false}
	    else if ($scope.getNumberFittedDatasets()<$scope.getNumberDatasetsToFit()) {
		return true
	    } else if ($scope.getNumberFittedDatasets()==$scope.getNumberDatasetsToFit()) {
		$scope.fitComplete = true;
		return false
	    }
	}

	// The function to mark the current SVG view to download
	$scope.toDownloads = function() {
	    var d = new Date()
	    var date_fmt = d.getDate()+'-'+(d.getMonth()+1)+'-'+d.getFullYear()+' '+d.getHours()+":"+d.getMinutes()
	    var displayPars = {pdfcdf: $scope.displayCDF,
			       fit:$scope.jlfit[$scope.ce-1]!==null& !$scope.showJLP,
			       fitP: $scope.showJLPf,
			       jldP: $scope.showJLP,
			       MaxJump: $scope.maxJumpSlider.value,
			       displayedDataset: $scope.showJLP? null : $scope.ce}
	    var dwnlPars = {svg : $('#mainHist').html(),
			    cell : $scope.datasets[$scope.ce-1].id,
			    jldParams : angular.copy($scope.jldParameters),
			    fitParams : angular.copy($scope.modelingParameters),
			    jld : angular.copy($scope.jlhist),
			    jldp: angular.copy($scope.jlphist),
			    fit : angular.copy($scope.jlfit),
			    fitp: angular.copy($scope.jlpfit),
			    description: $scope.downloadPopover.description,
			    name: $scope.downloadPopover.name,
			    date: date_fmt,
			    display: angular.copy(displayPars)}
	    downloadService.setDownload(dwnlPars);
	    $scope.downloadPopover.isOpen = false;
	}

	$scope.downloadPopover = {
	    isOpen: false,
	    templateUrl: 'myPopoverTemplate.html',
	    description: '',
	    name: '',
	    open: function open() {
		$scope.downloadPopover.isOpen = true;
            }
	};

	// Test function to get the nearest fit for the z correction
	$scope.$watch('modelingParameters', function(params, oldparams) {
	    if (angular.equals(params, oldparams)) {return}
	    getterService.getNearestZcorr(params.dZ, params.dT).then(
		function(ret) {
		    //console.log(ret)
		    $scope.modelingParameters.dTfit = ret.dT
		    $scope.modelingParameters.dZfit = ret.dZ
		    $scope.zcorr.a = ret.params[0]
		    $scope.zcorr.b = ret.params[1]
		}
	    )
	}, true);

	refreshMaxJumpSlider = function () {
	    $timeout(function () {
		$scope.$broadcast('rzSliderForceRender');
	    });
	}
    }]);
