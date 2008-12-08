// check that search term has been provided
if (args.q == undefined || args.q.length == 0)
{
   status.code = 400;
   status.message = "Search term has not been provided.";
   status.redirect = true;
}
else
{
   // perform search
   var nodes = search.luceneSearch(args.q);
   results = []
   for (i=0; i < nodes.length; i =i+1){
		if(nodes[i].isDocument){
			results[i] = nodes[i];
		}
	}
   
   model.resultset = results;
   
   
}
