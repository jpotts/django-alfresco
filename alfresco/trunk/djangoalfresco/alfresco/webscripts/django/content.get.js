

var contentId = args.id;
var doc = search.findNode("workspace://SpacesStore/" + contentId );

if (doc == undefined)
{
   status.code = 404;
   status.message = "Document " + contentId + " not found.";
   status.redirect = true;
} 
else {
	model.doc = doc;
}