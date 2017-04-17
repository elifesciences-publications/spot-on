var url = "http://127.0.0.1:8000/SPTGUI/analysis/sparkling-unit-1656/api/jld_default/1019"

var svg = d3.select("svg"),
    margin = {top: 10, right: 20, bottom: 40, left: 10},
    width = +svg.attr("width") - margin.left - margin.right,
    height = +svg.attr("height") - margin.top - margin.bottom,
    g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");

var color = d3.scaleLinear()
    .domain([-1, 0,1])
    .range(["red", "yellow", "green"])

d3.json(url, function(error, dat) {
    if (error) throw error;
    dat = dat.jld
    //dat[1] = dat[1].filter(function(el,i){return (i<6)})
    
    // Create data object
    data_mult = dat[1].map(function(jld) {
	var da = []
	for (i=1; i<dat[0].length; i++) {
	    da.push({date: dat[0][i-1], close: jld[i-1]});
	    da.push({date: dat[0][i], close: jld[i-1]});
	}
	return da
    })
    n_dt = data_mult.length // number of dt

    // Prepare display
    var x = d3.scaleLinear().rangeRound([0, width]);
    if (n_dt>1) {
	var y = d3.scaleLinear().rangeRound([1.5*height/n_dt, 0]);
	var skl = .5
    } else {
	var y = d3.scaleLinear().rangeRound([height/n_dt, 0]);
	var skl = 0
    }
    var yfull = d3.scaleLinear().rangeRound([height, 0]);    

    var area = d3.area()
	.x(function(d) { return x(d.date); })
	.y1(function(d) { return y(d.close); })
	.y0(function(d) {return y(0);});

    maxy = data_mult.map(function(v) {return d3.max(v, function(d) { return d.close; })})
    x.domain([0, d3.max(data_mult[0], function(d) { return d.date; })]);
    y.domain([0, 1.1*d3.max(maxy)]);

    // Display
    console.log("Displaying "+n_dt+" histograms")
    var incr=height/n_dt;
    data_mult.forEach(function(data, i ) {
	rat = (n_dt+i-2)/(n_dt+i-1)*incr
	rat2 = i*rat+incr*1.5
	g.append("path") // Add the histogram
	    .attr("transform", "translate(0," + (i*rat) + ")")
	    .datum(data)
	    .attr("fill", color(i/n_dt*2-1))
	    .attr("d", area)
	g.append("g")
	    .append("text")
	    .attr("fill", "#000")
	    .attr("transform", "translate("+0.8*width+","+ (rat2-.1*incr) +")")
	    .attr("text-anchor", "middle")
	    .text("\u0394\u03C4 = "+(i+1) + " dt")

	if (i+1 != data_mult.length) {
	    g.append("g")
		.attr("transform", "translate(0," + rat2 + ")")
		.call(d3.axisBottom(x).ticks(0))
	} else {
	    g.append("g")
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
});


