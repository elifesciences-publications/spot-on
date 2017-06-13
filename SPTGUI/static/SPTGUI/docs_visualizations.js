// A module to display a few visualizations in the docs.
;(function(window) {
    // From https://thinkster.io/angular-tabs-directive
    angular.module('app', ['rzModule','toggle-switch'])
})(window);

angular.module('app')
    .directive('jumpLengthDistribution', function() {
	var csvReady = false;
	var abParams = null;

	function distrib(x, D, sigma, dt) {
	    return x.map(function(xx) {return xx/(2*(dt*D+sigma*sigma))*Math.exp(-1*xx*xx/(4*(dt*D+sigma*sigma)))
				      })
	}

	function C_AbsorBoundAUTO(z, CurrTime, D, halfZ) {
	    WhenToStop = Math.pow(10,-7)
	    f = Infinity
	    n = 0
	    h = 1
	    
	    while (Math.abs(f) > WhenToStop) {
		if (CurrTime != 0) {
		    z1 =  ((2*n+1)*halfZ-z)/Math.pow(4*D*CurrTime, 0.5)
		    z2 =  ((2*n+1)*halfZ+z)/Math.pow(4*D*CurrTime, 0.5)
		}
		else if ((2*n+1)*halfZ-z<0) {
		    z1 = -Infinity
		    z2 = Infinity
		} else {
		    z1 = Infinity
		    z2 = Infinity
		}
		
		f = Math.pow(-1, n) * ( erfc(z1) +  erfc(z2) )
		h -= f
		n += 1
	    }
	    return h	    
	}
	
	function zcorr(dZ, D, dt) {
	    // Deparse
	    DeltaZ_use = dZ;
	    D_FREE = D;
	    curr_dT = dt
	    
	    nsteps = 80.0
	    HalfDeltaZ_use = DeltaZ_use/2.0
	    stp  = DeltaZ_use/nsteps
	    xint = d3.range(nsteps).map(function(i){return -HalfDeltaZ_use+i*stp;})
	    yint = xint.map(function(i) {
		return C_AbsorBoundAUTO(i, curr_dT, D_FREE, HalfDeltaZ_use)*stp
	    })
	    Z_corr = 0
	    yint.forEach(function(i) {Z_corr = Z_corr + i})
	    return Z_corr* 1/DeltaZ_use
	}
	
	function link(scope, el, attr) {
	    // Main plot function
	    function plot(dat) {
		// Compute stuff
		D1 = dat.D1 // 5
		D2 = dat.D2 // .1
		P = dat.P // 0.5
		dt = dat.dt/1000 // 0.01
		sigma = dat.S/1000 //35/1000.0
		showTheo = dat.theo

		var dZ = parseFloat(abParams[0][" dZ"])
		var a = null;
		var b = null;
		abParams.forEach(function(el) {
		    if (Math.abs(parseFloat(el.dT)-dt)<0.00001) {
			a = parseFloat(el[" a"])// yes, this is awful.
			b = parseFloat(el[" b"])
		    }
		})
		dZcorr1 = dZ + a*Math.sqrt(D1) + b
		dZcorr2 = dZ + a*Math.sqrt(D2) + b
		console.log(dZcorr1 + " " + a + " " + b)
		dZC1 = zcorr(dZcorr1, D1, dt)
		dZC2 = zcorr(dZcorr2, D2, dt)

		x_range = [0, 3] // µm
		X = d3.range(x_range[0], x_range[1], x_range[1]/300)
		Y1 = distrib(X, D1, sigma, dt)
		XY1 = X.map(function(xx, i) {return {x: xx, y:P*Y1[i]}})
		Y2 = distrib(X, D2, sigma, dt)
		XY2 = X.map(function(xx, i) {return {x: xx, y:(1-P)*Y2[i]}})
		XY12 = X.map(function(xx, i) {return {x: xx, y:P*Y1[i]+(1-P)*Y2[i]}})

		ZC1 = X.map(function(xx, i) { // Z Corrected 
		    return {x:xx, y:P*Y1[i]*dZC1}})
		ZC2 = X.map(function(xx, i) {
		    return {x:xx, y:(1-P)*Y2[i]*dZC2}})
		ZC12 = X.map(function(xx, i) {
		    return {x:xx, y: ZC1[i].y + ZC2[i].y}})

		// Clean plot
		g.selectAll("g").remove()
		
		// Prepare plot
		var x = d3.scaleLinear().rangeRound([0, width]);
		var y = d3.scaleLinear().rangeRound([height, 0]);
 		x.domain(x_range);
		if (showTheo) {
 		    y.domain([0, d3.max(XY12.map(function(xy, i){
			return Math.max(XY1[i].y, XY2[i].y, XY12[i].y)}))]);
		} else {
 		    y.domain([0, d3.max(ZC12.map(function(xy, i){
			return Math.max(ZC1[i].y, ZC2[i].y, ZC12[i].y)}))]);
		}
		var lines = g.append("g");
		var Aaxis = g.append("g")
		var line = d3.line()
 	    	    .curve(d3.curveBasis)
 		    .x(function(d) { return x(d.x); })
 		    .y(function(d) { return y(d.y); });

		function plotLine(lines, dat, col, wdth, gap) {
		    lines.append("path")
	    		.datum(dat)
 	    		.attr("fill", "none")
 	    		.attr("stroke", col)
 	    		.attr("stroke-width", wdth)
			.style("stroke-dasharray", (""+gap+" "+gap))
 	    		.attr("d", line)
		}
		
		// DRAW!!!
		if (showTheo) {
		    plotLine(lines, XY12, "orange", 4, 0)
		    plotLine(lines, XY1, "red", 2.5, 0)
		    plotLine(lines, XY2, "blue", 2.5, 0)
		}
		plotLine(lines, ZC12, "orange", 4, 4)
		plotLine(lines, ZC1, "red", 2.5, 4)
		plotLine(lines, ZC2, "blue", 2.5, 4)

		// Some legends
		Aaxis.append("g")
		    .attr("transform", "translate(0," + height + ")")
		    .call(d3.axisBottom(x))
		    .append("text")
		    .attr("fill", "#000")
		    .attr("transform", "translate("+width/2+","+ "30" +")")
		    .attr("text-anchor", "middle")
		    .text("jump distance (µm)")	    

		Aaxis.append("g")
	    	    .call(d3.axisLeft(y))
	    	    .append("text")
	    	    .attr("fill", "#000")
	    	    .attr("dy", "-1em")
	    	    .attr("text-anchor", "end")
	    	    .text("P(r)");
		
		p1 = [18, 36, 36+18]
		co = ['red', 'blue', 'orange']
		na = ["D1="+D1+" µm²/s", "D2="+D2+" µm²/s", "Two components"]
		if (showTheo) {
		    scl = 2;
		    dp = 1.5*(p1[1]-p1[0])
		} else {
		    scl = 1;
		    dp = 1.5*(p1[1]-p1[0])
		}
		for (var i=0;i<p1.length;i++) {
		    if (showTheo) {
			Aaxis.append("rect")
			    .attr("x", width - 18)
			    .attr("y", scl*p1[i])
			    .attr("width", 14)
			    .attr("height", 14)
			    .style("fill", co[i]);
			Aaxis.append("text")
			    .attr("x", width - 36)
			    .attr("y", scl*p1[i])
			    .attr("dy", ".75em")
			    .style("text-anchor", "end")
			    .text(na[i] + " ground truth");
		    }
		    Aaxis.append("line")
		        .attr("x1", width - 24)
			.attr("x2", width)
			.attr("y1", scl*p1[i] + dp)
			.attr("y2", scl*p1[i] + dp)
			.style("stroke-dasharray","5,5")//dashed array for line
			.style("stroke", co[i]);
		    Aaxis.append("text")
			.attr("x", width - 36)
			.attr("y", scl*p1[i] + dp/1.5)
			.attr("dy", ".75em")
			.style("text-anchor", "end")
			.text(na[i]+" observed");
		}
	    }
	    
	    
	    // Prepare the SVG canvas
	    var svg = d3.select(el[0]).append('svg')
	    margin = {top: 20, right: 20, bottom: 50, left: 30},
 	    width = 600;
 	    height = 300;	    
 	    svg.attr("width", width).attr("height", height);
	    width = width - margin.left - margin.right;
	    height = height - margin.top - margin.bottom;

	    var g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");

	    // Get the data
	    d3.csv("/static/SPTGUI/zcorr.csv", function(error, data) {
		if (error) throw error;
		abParams = data
		csvReady = true
		plot({D1: 5, D2: 1, P: 0.5, dt: 10, S: 35, theo: true}) // Should match the default in the HTML file

	    })
	    
	    scope.$watch('data', function(dat){
		if (!csvReady) {return;}
		plot(dat)
	    }, true)
	}
	return {
	    link: link,
	    restrict: 'E',
	    scope: {data: '='}
	};
    })
