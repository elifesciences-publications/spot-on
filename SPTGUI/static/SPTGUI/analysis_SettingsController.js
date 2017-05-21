angular.module('app')
    .controller('SettingsController', ['MainSocket', '$scope', '$window', function(MainSocket, $scope, $window) {
	erase = function() {
	    var promise = MainSocket.sendRequest({type: "erase"})
	    return promise
	}
	
	$scope.erase = function() {
	    // Function to erase the analysis
	    alert("It's already too late. There is no way back...")
	    erase().then(function(resp) {
		alert("Your data is now gone with the wind")
		console.log(resp)
		$window.location=resp;
	    })
	}

    }])
