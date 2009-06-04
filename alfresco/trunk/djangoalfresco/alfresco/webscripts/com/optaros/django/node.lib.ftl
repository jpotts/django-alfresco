<#assign datetimeformat="EEE, dd MMM yyyy HH:mm:ss zzz">
<#--
Renders a node as a JSON object
-->
<#macro nodeJSON result>
<#escape x as jsonUtils.encodeJSONString(x)>
{
"pk": "${result.doc.id}",
"model": "alfresco.content", 
"fields": {
"name" : "<#if result.doc.properties['name']?exists> ${result.doc.properties['name']}</#if>",
"content_type"  : "${result.doc.properties.content.mimetype}",
"title" : "<#if result.doc.properties['title']?exists> ${result.doc.properties['title']}</#if>",
"description" : "<#if result.doc.properties['description']?exists> ${result.doc.properties['description']}</#if>",
"author" : "<#if result.doc.properties['author']?exists> ${result.doc.properties['author']}</#if>",
"created" : <#if result.doc.properties['created']?exists>${result.doc.properties['created']?string("yyyy-MM-dd")}</#if>,
"modified" : <#if result.doc.properties['modified']?exists>${result.doc.properties['modified']?string("yyyy-MM-dd")}</#if>,
"content" : "<#if result.doc.properties.content.mimetype?substring(0,4) == 'text'>${result.doc.content}<#else><a href='${url.serviceContext}/api/node/content/${result.doc.nodeRef.storeRef.protocol}/${result.doc.nodeRef.storeRef.identifier}/${result.doc.nodeRef.id}/${result.doc.name?url}'>${result.doc.name}</a></#if>",
"url" : "${url.serviceContext}/api/node/content/${result.doc.nodeRef.storeRef.protocol}/${result.doc.nodeRef.storeRef.identifier}/${result.doc.nodeRef.id}/${result.doc.name?url}",
"space"  : "${result.doc.parent.id}",
"tags" : "<#list result.tags as tag>${tag}<#if tag_has_next>,</#if></#list>"
}}
</#escape>
</#macro>

<!--
Renders a node as an XML object
-->
<#macro nodeXML result>
<object pk="${result.doc.id}" model="alfresco.content">
	<field type="CharField" name="name"><#if result.doc.properties['name']?exists> ${result.doc.properties['name']}</#if></field>
   	<field type="CharField" name="space">${result.doc.parent.id}</field>
   	<field type="CharField" name="mimetype">${result.doc.properties.content.mimetype}</field>
	<field type="CharField" name="size">${result.doc.properties.content.size}</field>
	<field type="CharField" name="description"><#if result.doc.properties['description']?exists> ${result.doc.properties['description']}</#if></field>
	<field type="CharField" name="title"><#if result.doc.properties['title']?exists> ${result.doc.properties['title']}</#if></field>
	<field type="CharField" name="author"><#if result.doc.properties['author']?exists> ${result.doc.properties['author']}</#if></field>
	<field type="TextField" name="content"><![CDATA[<#if result.doc.properties.content.mimetype?substring(0,4) == 'text'>${result.doc.content}<#else><a href='${url.serviceContext}/api/node/content/${result.doc.nodeRef.storeRef.protocol}/${result.doc.nodeRef.storeRef.identifier}/${result.doc.nodeRef.id}/${result.doc.name?url}'>${result.doc.name}</a></#if>]]></field>
	<field type="DateField" name="created"><#if result.doc.properties['created']?exists>${result.doc.properties['created']?string("yyyy-MM-dd")}</#if></field>
	<field type="DateField" name="modified"><#if result.doc.properties['modified']?exists>${result.doc.properties['modified']?string("yyyy-MM-dd")}</#if></field>
	<field type="CharField" name="url">${url.serviceContext}/api/node/content/${result.doc.nodeRef.storeRef.protocol}/${result.doc.nodeRef.storeRef.identifier}/${result.doc.nodeRef.id}/${result.doc.name?url}</field>
	<field type="CharField" name="tags"><#list result.tags as tag>${tag}<#if tag_has_next>,</#if></#list></field>
</object>
</#macro>