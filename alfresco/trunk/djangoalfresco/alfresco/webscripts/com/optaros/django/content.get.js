//
// Copyright 2008 Optaros, Inc.
//
var contentId = args.id;
var doc = search.findNode("workspace://SpacesStore/" + contentId );

if (doc == undefined)
{
   status.code = 404;
   status.message = "Document " + contentId + " not found.";
   status.redirect = true;
} 
else {
	var result = new Result(doc, doc.tags);
	model.result = result;
}

function Result(doc, tags) {
	this.doc = doc;
	this.tags = tags;
}