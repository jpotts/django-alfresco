[
<#list results as result>
{"pk": "${result.doc.id}", 
"model": "alfresco.content", 
"fields": {
"name" : "${result.doc.name}",
"description" : "<#if result.doc.properties['description']?exists> ${result.doc.properties['description']}</#if>",
"content" : "<#if result.doc.properties.content.mimetype?substring(0,4) == 'text'>${result.doc.content}<#else><a href='${url.serviceContext}/api/node/content/${result.doc.nodeRef.storeRef.protocol}/${result.doc.nodeRef.storeRef.identifier}/${result.doc.nodeRef.id}/${result.doc.name?url}'>${result.doc.name}</a></#if>",
"url" : "${url.serviceContext}/api/node/content/${result.doc.nodeRef.storeRef.protocol}/${result.doc.nodeRef.storeRef.identifier}/${result.doc.nodeRef.id}/${result.doc.name?url}",
"space" : "${result.doc.parent.id}",
"tags" : "<#list result.tags as tag>${tag}<#if tag_has_next>,</#if></#list>"
}}
<#if result.doc.id != results?last.doc.id>,</#if>
</#list>
]
