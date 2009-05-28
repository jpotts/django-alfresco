[
<#list resultset as result>
{"pk": "${result.doc.id}",
"fields": {
"name" : "<#if result.doc.properties['name']?exists> ${result.doc.properties['name']}</#if>",
"content_type"  : "${result.doc.properties.content.mimetype}",
"title" : "<#if result.doc.properties['title']?exists> ${result.doc.properties['title']}</#if>",
"description" : "<#if result.doc.properties['description']?exists> ${result.doc.properties['description']}</#if>",
"author" : "<#if result.doc.properties['author']?exists> ${result.doc.properties['author']}</#if>",
"created" : <#if result.doc.properties['created']?exists>${result.doc.properties['created']?string("yyyy-MM-dd")}</#if>,
"modified" : <#if result.doc.properties['modified']?exists>${result.doc.properties['modified']?string("yyyy-MM-dd")}</#if>,
"url" : "${url.serviceContext}/api/node/content/${result.doc.nodeRef.storeRef.protocol}/${result.doc.nodeRef.storeRef.identifier}/${result.doc.nodeRef.id}/${result.doc.name?url}",
"space"  : "${result.doc.parent.id}",
"tags" : "<#list result.tags as tag>${tag}<#if tag_has_next>,</#if></#list>"
}}
<#if result.doc.id != resultset?last.doc.id>,</#if>
</#list>
]
