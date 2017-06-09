angular.module('app')
    .directive('jumpLengthHistogram', function() {
	function adjustTextLabels(selection) {
	    selection.selectAll('.tick text')
		.attr('transform', 'translate(0,7)');
}
	function fmt_data(dat_raw, cdf, maxjump) {
	    dat = angular.copy(dat_raw)
	    data = [];
	    for (i=1; i<dat[0].length; i++) {
		if (dat[0][i]<= maxjump) {
		    if (cdf) {
			dat[1][i] = dat[1][i-1]+dat[1][i]
			data.push({date: dat[0][i-1], close: dat[1][i-1]});
			data.push({date: dat[0][i], close: dat[1][i-1]});
		    } else {
			data.push({date: dat[0][i-1], close: dat[1][i-1]});
			data.push({date: dat[0][i], close: dat[1][i-1]});
		    }
		}
	    }
	    return data;
	};
	function fmt_fit(x,y_raw, cdf, maxjump, ds) {
	    if (cdf) {
		y = cumsum(angular.copy(y_raw), ds)
	    } else {
		y = y_raw
	    }
	    data = [];
	    for (i=0; i<x.length; i++) {
		if (x[i] <= maxjump) {
		    data.push({x: x[i], y: y[i]});
		}
	    }
	    return data;	    
	};
	function precsum(d) {
	    ds = 0.0
	    for (i=1;i<d.length;i++) {
		ds += d[i]
	    }
	    return ds
	}
	function cumsum(d, ds) {
	    for (i=0;i<d.length;i++) {
		d[i]=d[i]/ds
	    }
	    for (i=1;i<d.length;i++) {
		d[i]=d[i-1]+d[i]
	    }
	    return d
	};
	var color = d3.scaleLinear()
	    .domain([-1, 0,1])
	    .range(["red", "yellow", "green"])
	
	function link(scope, el, attr){
	    // Prepare the SVG canvas
	    var svg = d3.select(el[0]).append('svg')
	    margin = {top: 20, right: 20, bottom: 50, left: 10},
	    width = 900;
	    height = 800;
	    
	    svg.attr("width", width).attr("height", height);
	    width = width - margin.left - margin.right;
	    height = height - margin.top - margin.bottom;
	    g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");	

	    var bars = g.append("g");
	    var fitline = g.append("g");
	    var fitlinepooled = g.append("g");
	    var legend = g.append("g");
	    var leftaxis = g.append("g")
	    var horiaxis = bars.append("g")
	    scope.$watch('data', function(dat){ // Angular connexion
		// Clear
		bars.selectAll("path").remove()
		legend.selectAll("g").remove()
		horiaxis.selectAll("g").remove()
		fitline.selectAll("path").remove()
		fitlinepooled.selectAll("path").remove()
		
		// Parse inputs
		if(!dat){ return; }
		if(!dat[0]){ return; }
		
		if (dat[4]&!dat[5]) {
		    pool = true;
		    data_id = 3
		} else {
		    pool = false;
		    data_id = 0
		}
		cdf = dat[9]
		maxjump = dat[10]
		
		// define functions
		var area = d3.area()
		    .x(function(d) { return x(d.date); })
		    .y1(function(d) { return y(d.close); })
		    .y0(function(d) {return y(0);});
		
		var line = d3.line()
	    	    .curve(d3.curveBasis)
		    .x(function(d) { return x(d.x); })
		    .y(function(d) { return y(d.y); });
		
		// Compute data structure
		data_mult = scope.data[data_id][1].map(function(el, i) {
		    return fmt_data([scope.data[data_id][0], el], cdf, maxjump)
		})
		n_dt = data_mult.length // number of dt
		
		// Prepare display
		var x = d3.scaleLinear().rangeRound([0, width]);
		if (n_dt>1) {
		    var y = d3.scaleLinear().rangeRound([1.5*height/n_dt, 0]);
		} else {
		    var y = d3.scaleLinear().rangeRound([height/n_dt, 0]);
		}
		var yfull = d3.scaleLinear().rangeRound([height, 0]);    

		leftaxis.selectAll("g").remove()
		leftaxis.append("g")
	    	    .call(d3.axisLeft(yfull).ticks(0))
	    	    .append("text")
	    	    .attr("fill", "#000")
	    	    .attr("transform", "rotate(-90)")
	    	    .attr("y", 10)
	    	    .attr("dy", "0.71em")
	    	    .attr("text-anchor", "end")
	    	    .text("P(r)");
		
		maxy = data_mult.map(function(v) {
		    return d3.max(v, function(d) { return d.close; })})
		x.domain([0, d3.max(data_mult[0], function(d) {
		    return d.date; })]);
		y.domain([0, 1.1*d3.max(maxy)]);
		
		// CDF-specific changes
		if (cdf) {ratcdf = .9}
		else {ratcdf = .1}

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
			.attr("transform", "translate("+0.8*width+","+ (rat2-ratcdf*incr) +")")
			.attr("text-anchor", "middle")
			.text("\u0394\u03C4 = "+(i+1) + " dt")
		
		    if (i+1 != data_mult.length) {
			horiaxis.append("g") // This will fail
			    .attr("transform", "translate(0," + rat2 + ")")
			    .call(d3.axisBottom(x).ticks(0))
		    } else {
			horiaxis.append("g")
			    .attr("transform", "translate(0," + rat2 + ")")
			    .call(d3.axisBottom(x)).call(adjustTextLabels)
			    .append("text")
			    .attr("fill", "#000")
			    .attr("transform", "translate("+width/2+","+ "35" +")")
			    .attr("text-anchor", "middle")
			    .text("jump distance (µm)")	    
		    }
		    // Handle fit plotting
		    if (dat[1] && !pool) { // Add the line graph of the fit
			fit = dat[1].fit;
			fitline.append("path")
			    .attr("transform", "translate(0," + (i*rat) + ")")
		    	    .datum(fmt_fit(fit.x,
					   fit.y[i],
					   cdf,
					   maxjump,
					   precsum(fit.y[i])))
			    .attr("fill", "none")
			    .attr("stroke", "black")
			    .attr("stroke-width", 1.5)
			    .attr("d", line);
		    }

		    // Handle pooled fit plotting
		    if (dat[7]) { // Show the pooled fit
			if (!dat[6]) {
			    console.log("No pooled fit provided but told to plot it. This is impossible.")
			    return;
			}
			fit = dat[6].fit;
			fitlinepooled.append("path")
			    .attr("transform", "translate(0," + (i*rat) + ")")
		    	    .datum(fmt_fit(fit.x,
					   fit.y[i],
					   cdf,
					   maxjump,
					   precsum(fit.y[i])))
			    .attr("fill", "none")
			    .attr("stroke", "grey")
			    .attr("stroke-width", 3)
			    .style("stroke-dasharray", ("6, 6"))
			    .attr("d", line);
		    }
		})
		if (pool) {
		    bars.selectAll("path").attr("stroke", "black")
		}
		    
	    }); 
	}
	return {
	    link: link,
	    restrict: 'E',
	    scope: {data: '='}
	};
	})
	    

