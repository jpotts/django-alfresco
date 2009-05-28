[{"pk": "${doc.id}", 
"model": "alfresco.content", 
"fields": {
"name" : "${doc.properties.name}",
"content_type"  : "${doc.properties.content.mimetype}",
"description" : "<#if doc.properties['description']?exists> ${doc.properties['description']}</#if>",
"title" : "<#if doc.properties['title']?exists> ${doc.properties['title']}</#if>",
"author" : "<#if doc.properties['author']?exists> ${doc.properties['author']}</#if>",
"content" : "<#if doc.properties.content.mimetype?substring(0,4) == 'text'>${doc.content}<#else><a href='${url.serviceContext}/api/node/content/${doc.nodeRef.storeRef.protocol}/${doc.nodeRef.storeRef.identifier}/${doc.nodeRef.id}/${doc.name?url}'>${doc.name}</a></#if>",
"url" : "${url.serviceContext}/api/node/content/${doc.nodeRef.storeRef.protocol}/${doc.nodeRef.storeRef.identifier}/${doc.nodeRef.id}/${doc.name?url}",
"space"  : "${doc.parent.id}",
"tags" : "<#list tags as tag>${tag}<#if tag_has_next>,</#if></#list>"
}}]
