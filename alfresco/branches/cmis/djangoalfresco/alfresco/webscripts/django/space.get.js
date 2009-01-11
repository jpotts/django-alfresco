
var num_entries = parseInt(args.num);

var node_id = args.id;
var path_node = search.findNode("workspace://SpacesStore/" + node_id );

if (path_node == undefined)
{
   status.code = 404;
   status.message = "Space " + node_id + " not found.";
   status.redirect = true;
} 

// If the node doesn't exist just exit. Nulls should be handled in the presentation layer
else{
	//Place all the documents in the model
	//
	//model: An empty associative array which may be populated by the JavaScript. Values placed 
	//into this array are available as root objects in web script response templates.
	
	var docs = [];
	var length =path_node.children.length
	if(num_entries){length = num_entries;}
	for (i=0; i < length; i =i+1){
		if(path_node.children[i].isDocument){
			docs[i] = path_node.children[i];
		}
	}
	model.docs = docs
}