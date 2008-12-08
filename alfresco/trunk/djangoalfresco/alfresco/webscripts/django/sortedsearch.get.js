var page = parseInt(args.page);
var page_size = parseInt(args.page_size);
var limit = parseInt(args.limit);
var sort_by = args.sort_by;
var q = args.q;
var sort_order = true;

if (q == undefined || q.length == 0){
   status.code = 400;
   status.message = "Search term has not been provided.";
   status.redirect = true;
}
else if (sort_by == undefined){
   status.code = 400;
   status.message = "Sort by has not been provided.";
   status.redirect = true;
}
else{
	//sort_by looks like '-title' for descending queries 
	if (sort_by.substring(0,1) == '-'){
		sort_order= false;
		sort_by = sort_by.substring(1);
	}
	
	//Make sure we are only bringing back content
	q = q + ' AND TYPE:"cm:content"'
	
	// Actual Search
	var script_nodes = search.luceneSearch(q, '@cm:' + sort_by , sort_order) 
	
	var docs = [];
	var start = 0;
	var stop = script_nodes.length;
	var num_results = script_nodes.length;
	
	// if both page and page_size are set paginate results
	if ( !isNaN(page) && !isNaN(page_size)){
		start = (page - 1) * page_size;
		end_page = start + page_size;
		if (end_page < stop){
			stop = end_page;
		} 
	}
	// If a limit is set, honor it
	else if ( !isNaN(limit) && limit < stop){
		stop = limit;
	}
	
	//Get Docs
	for( i= start; i < stop; i = i+1){
		docs[i] = script_nodes[i];
	}
	
	model.q = q;
	model.sort_by = sort_by;
	model.page = page;
	model.page_size = page_size;
	model.start_index = start;
	model.stop_index = stop;
	model.num_results = num_results;
	var num_pages = parseInt(num_results/page_size);
	if (num_results % page_size != 0 ){
		num_pages = num_pages +1;
	}
	model.num_pages = num_pages;
	model.resultset = docs;
}