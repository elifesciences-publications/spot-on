var url = "/SPTGUI/analysis/toto/api/analyze/160?bin_size=10&random=3&include=153%2C154%2C155%2C156%2C157%2C158%2C159%2C160&hashvalue=bin_size%3D10%26random%3D3%26include%3D153%252C154%252C155%252C156%252C157%252C158%252C159%252C160%26hashvalue%3Dnull"

var demourl = "/static/SPTGUI/data.tsv";

var svg = d3.select("svg"),
    margin = {top: 20, right: 20, bottom: 30, left: 50},
    width = +svg.attr("width") - margin.left - margin.right,
    height = +svg.attr("height") - margin.top - margin.bottom,
    g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");

var parseTime = d3.timeParse("%d-%b-%y");

var x = d3.scaleLinear()
    .rangeRound([0, width]);

var y = d3.scaleLinear()
    .rangeRound([height, 0]);

var area = d3.area()
    .x(function(d) { return x(d.date); })
    .y1(function(d) { return y(d.close); })
    .y0(function(d) {return y(0);});

//d3.tsv(demourl, function(d) {
    //d.date = parseTime(d.date);
    //d.close = +d.close;
//    return d;
d3.json(url, function(error, dat) {
    // Create data object
    data = [];
    data.push({date: 0, close: 0});
    for (i=1; i<dat[0].length; i++) {
	data.push({date: dat[0][i-1], close: dat[1][0][i]});
	data.push({date: dat[0][i], close: dat[1][0][i]});
    }
    
    console.log(data);
    if (error) throw error;
    console.log(data);
    x.domain([0, d3.max(data, function(d) { return d.date; })]);
    y.domain([0, d3.max(data, function(d) { return d.close; })]);
    //area.y0(100);

    g.append("path")
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
});


