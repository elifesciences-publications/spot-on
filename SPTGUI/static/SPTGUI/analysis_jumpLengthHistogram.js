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
	function link(scope, el, attr){
	    // Get input and parse it
	    if (!scope.data[0]){return;}
	    
	    dt = scope.data[2];
	    data = fmt_data([scope.data[0][0], scope.data[0][1][dt]]);
	    
	    var svg = d3.select(el[0]).append('svg')
	    margin = {top: 20, right: 20, bottom: 30, left: 50},
	    width = 600;
	    height = 400;
	    
	    svg.attr("width", width).attr("height", height);
	    width = width - margin.left - margin.right; //+svg.attr("width")
	    height = height - margin.top - margin.bottom; // +svg.attr("height")
	    g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");

	    var x = d3.scaleLinear().rangeRound([0, width]);
	    var y = d3.scaleLinear().rangeRound([height, 0]);

	    var area = d3.area()
		.x(function(d) { return x(d.date); })
		.y1(function(d) { return y(d.close); })
		.y0(function(d) {return y(0);});
	    
	    var line = d3.line()
		.x(function(d) { return x(d.x); })
		.y(function(d) { return y(d.y); });

	    x.domain([0, d3.max(data, function(d) { return d.date; })]);
	    y.domain([0, 1.1*d3.max(data, function(d) { return d.close; })]);

	    var bars = g.append("g");
	    var fitline = g.append("g");
	    var fitlinepooled = g.append("g");
	    fitline.append("path");
	    fitlinepooled.append("path");
	    bars.append("path")
		.datum(data)
		.attr("fill", "steelblue")
		.attr("d", area);

	    g.append("g")
		.attr("transform", "translate(0," + height + ")")
		.call(d3.axisBottom(x));

	    g.append("g")
		.call(d3.axisLeft(y))
		.append("text")
		.attr("fill", "#000")
		.attr("transform", "rotate(-90)")
		.attr("y", 6)
		.attr("dy", "0.71em")
		.attr("text-anchor", "end")
		.text("P(r)");

	    scope.$watch('data', function(dat){ // Angular connexion
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
		if (dt<data[1].length && dt>0) {
		    bars.selectAll("path")
			.datum(fmt_data([data[0], data[1][dt]]))
			.attr("fill", col)
			.attr("d", area);
		    
		}
		else {
		    bars.selectAll("path").attr("fill", "transparent");
		}
		// Handle fit plotting
		if (dat[1] && !pool) { // Add the line graph of the fit
		    fit = dat[1].fit;
		    fitline.selectAll("path")
		    	.datum(fmt_fit(fit.x, fit.y[dt]))
			.attr("fill", "none")
			.attr("stroke", "red")
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
	    

