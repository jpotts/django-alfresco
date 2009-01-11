[
<#list docs as doc>
{"pk": "${doc.id}", 
"model": "alfresco.content", 
"fields": {
"name" : "${doc.name}",
"description" : "<#if doc.properties['description']?exists> ${doc.properties['description']}</#if>",
"content" : "<#if doc.properties.content.mimetype?substring(0,4) == 'text'>${doc.content}<#else><a href='${url.serviceContext}/api/node/content/${doc.nodeRef.storeRef.protocol}/${doc.nodeRef.storeRef.identifier}/${doc.nodeRef.id}/${doc.name?url}'>${doc.name}</a></#if>",
"url" : "${url.serviceContext}/api/node/content/${doc.nodeRef.storeRef.protocol}/${doc.nodeRef.storeRef.identifier}/${doc.nodeRef.id}/${doc.name?url}",
"space" : "${doc.parent.id}"
}}
<#if doc.id != docs?last.id>,</#if>
</#list>
]
