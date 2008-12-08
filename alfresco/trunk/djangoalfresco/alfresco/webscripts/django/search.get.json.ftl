[
<#list resultset as doc>
{"pk": "${doc.id}",
"fields": {
"name" : "<#if doc.properties['name']?exists> ${doc.properties['name']}</#if>",
"content_type"  : "${doc.properties.content.mimetype}",
"title" : "<#if doc.properties['title']?exists> ${doc.properties['title']}</#if>",
"description" : "<#if doc.properties['description']?exists> ${doc.properties['description']}</#if>",
"author" : "<#if doc.properties['author']?exists> ${doc.properties['author']}</#if>",
"created" : <#if doc.properties['created']?exists>${doc.properties['created']?string("yyyy-MM-dd")}</#if>,
"modified" : <#if doc.properties['modified']?exists>${doc.properties['modified']?string("yyyy-MM-dd")}</#if>,
"url" : "${url.serviceContext}/api/node/content/${doc.nodeRef.storeRef.protocol}/${doc.nodeRef.storeRef.identifier}/${doc.nodeRef.id}/${doc.name?url}",
"space"  : "${doc.parent.id}"
}}
<#if doc.id != resultset?last.id>,</#if>
</#list>
]
