angular.module('app')
    .directive('jumpLengthHistogram', function() {
	function fmt_data(dat) {
	    data = [];
	    for (i=1; i<dat[0].length; i++) {
		data.push({date: dat[0][i-1], close: dat[1][i-1]});
		data.push({date: dat[0][i], close: dat[1][i-1]});
	    }
	    return data;
	};
	function fmt_fit(x,y) {
	    data = [];
	    for (i=0; i<x.length; i++) {
		data.push({x: x[i], y: y[i]});
	    }
	    return data;	    
	};
	var color = d3.scaleLinear()
	    .domain([-1, 0,1])
	    .range(["red", "yellow", "green"])
	
	function link(scope, el, attr){
	    // Get input and parse it
	    if (!scope.data[0]){return;}
	    
	    dt = scope.data[2];
	    data_mult = scope.data[0][1].map(function(el) {
		return fmt_data([scope.data[0][0], el])
	    })
	    n_dt = data_mult.length // number of dt
	    
	    // Prepare the SVG canvas
	    var svg = d3.select(el[0]).append('svg')
	    margin = {top: 20, right: 20, bottom: 50, left: 10},
	    width = 900;
	    height = 800;
	    
	    svg.attr("width", width).attr("height", height);
	    width = width - margin.left - margin.right;
	    height = height - margin.top - margin.bottom;
	    g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");

	    // Prepare display
	    var x = d3.scaleLinear().rangeRound([0, width]);
	    if (n_dt>1) {
		var y = d3.scaleLinear().rangeRound([1.5*height/n_dt, 0]);
	    } else {
		var y = d3.scaleLinear().rangeRound([height/n_dt, 0]);
	    }
	    var yfull = d3.scaleLinear().rangeRound([height, 0]);    
	

	    var area = d3.area()
		.x(function(d) { return x(d.date); })
		.y1(function(d) { return y(d.close); })
		.y0(function(d) {return y(0);});
	    
	    var line = d3.line()
	    	.curve(d3.curveBasis)
		.x(function(d) { return x(d.x); })
		.y(function(d) { return y(d.y); });

	    maxy = data_mult.map(function(v) {return d3.max(v, function(d) { return d.close; })})
	    x.domain([0, d3.max(data_mult[0], function(d) { return d.date; })]);
	    y.domain([0, 1.1*d3.max(maxy)]);

	    var bars = g.append("g");
	    var fitline = g.append("g");
	    var fitlinepooled = g.append("g");
	    var legend = bars.append("g");

	    // Display
	    console.log("Displaying "+n_dt+" histograms")
	    var incr=height/n_dt;
	    data_mult.forEach(function(data, i ) {
		rat = (n_dt+i-2)/(n_dt+i-1)*incr
		rat2 = i*rat+incr*1.5
		bars.append("path") // Add the histogram
		    .attr("transform", "translate(0," + (i*rat) + ")")
		    .datum(data)
		    .attr("fill", color(i/n_dt*2-1))
		    .attr("d", area)
		legend.append("g")
		    .append("text")
		    .attr("fill", "#000")
		    .attr("transform", "translate("+0.8*width+","+ (rat2-.1*incr) +")")
		    .attr("text-anchor", "middle")
		    .text("\u0394\u03C4 = "+(i+1) + " dt")
		
		if (i+1 != data_mult.length) {
		    legend.append("g")
			.attr("transform", "translate(0," + rat2 + ")")
			.call(d3.axisBottom(x).ticks(0))
		} else {
		    legend.append("g")
			.attr("transform", "translate(0," + rat2 + ")")
			.call(d3.axisBottom(x))
			.append("text")
			.attr("fill", "#000")
			.attr("transform", "translate("+width/2+","+ "30" +")")
			.attr("text-anchor", "middle")
			.text("jump distance (µm)")	    
		}
	    })

	    g.append("g")
		.call(d3.axisLeft(yfull).ticks(0))
		.append("text")
		.attr("fill", "#000")
		.attr("transform", "rotate(-90)")
		.attr("y", 6)
		.attr("dy", "0.71em")
		.attr("text-anchor", "end")
		.text("P(r)");
	    
	    
	    fitline.append("path");
	    fitlinepooled.append("path");

	    scope.$watch('data', function(dat){ // Angular connexion
		// Parse inputs
		if(!dat){ return; }
		if(!dat[0]){ return; }
		dt = dat[2];
		
		if (dat[4]&!dat[5]) {
		    pool = true;
		    col = "orchid";
		    data = dat[3]
		} else {
		    pool = false;
		    col = "steelblue";
		    data = dat[0]
		}
		if (!dt) {return;}

		// Compute data structure
		data_mult = scope.data[0][1].map(function(el) {
		    return fmt_data([scope.data[0][0], el])
		})
		n_dt = data_mult.length // number of dt

		// Prepare display
		maxy = data_mult.map(function(v) {return d3.max(v, function(d) { return d.close; })})
		x.domain([0, d3.max(data_mult[0], function(d) { return d.date; })]);
		y.domain([0, 1.1*d3.max(maxy)]);

		// Clear
		bars.selectAll("path").remove()
		legend.selectAll("g").remove()

		// Display
		console.log("Redrawing "+n_dt+" histograms")
		var incr=height/n_dt;
		data_mult.forEach(function(data, i ) {
		    rat = (n_dt+i-2)/(n_dt+i-1)*incr
		    rat2 = i*rat+incr*1.5
		    bars.append("path") // Add the histogram
			.attr("transform", "translate(0," + (i*rat) + ")")
			.datum(data)
			.attr("fill", color(i/n_dt*2-1))
			.attr("d", area)
		    legend.append("g") // This will fail
			.append("text")
			.attr("fill", "#000")
			.attr("transform", "translate("+0.8*width+","+ (rat2-.1*incr) +")")
			.attr("text-anchor", "middle")
			.text("\u0394\u03C4 = "+(i+1) + " dt")
		
		    if (i+1 != data_mult.length) {
			legend.append("g") // This will fail
			    .attr("transform", "translate(0," + rat2 + ")")
			    .call(d3.axisBottom(x).ticks(0))
		    } else {
			legend.append("g")
			    .attr("transform", "translate(0," + rat2 + ")")
			    .call(d3.axisBottom(x))
			    .append("text")
			    .attr("fill", "#000")
			    .attr("transform", "translate("+width/2+","+ "30" +")")
			    .attr("text-anchor", "middle")
			    .text("jump distance (µm)")	    
		    }
		})
		
		// Handle fit plotting
		if (dat[1] && !pool) { // Add the line graph of the fit
		    fit = dat[1].fit;
		    fitline.selectAll("path")
		    	.datum(fmt_fit(fit.x, fit.y[dt]))
			.attr("fill", "none")
			.attr("stroke", "grey")
			.attr("stroke-width", 1.5)
			.attr("d", line);
		} else { // Erase the line
		    fitline.selectAll("path")
		    .attr("stroke", "transparent")
		}
		// Handle pooled fit plotting
		if (dat[7]) { // Show the pooled fit
		    fit = dat[6].fit;
		    fitlinepooled.selectAll("path")
		    	.datum(fmt_fit(fit.x, fit.y[dt]))
			.attr("fill", "none")
			.attr("stroke", "orange")
			.attr("stroke-width", 3)
			.style("stroke-dasharray", ("6, 6"))
			.attr("d", line);		    
		} else {
		    fitlinepooled.selectAll("path")
		    .attr("stroke", "transparent")		    
		}
	    }); 
	}
	return {
	    link: link,
	    restrict: 'E',
	    scope: {data: '='}
	};
	})
	    

