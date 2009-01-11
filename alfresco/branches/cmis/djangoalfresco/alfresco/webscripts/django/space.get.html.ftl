
<#list docs as doc>
	<h2>${doc.name}</h2>
	<h3><#if doc.properties['description']?exists> ${doc.properties['description']}</#if></h3>
	<h4><em><a href="/pluto/portal/Doc%20Detail?doc_id=${doc.id}">Article Detail</a></em></h4>
	<p>	
	<#if doc.properties.content.mimetype?substring(0,4) == 'text'>${doc.content}<#else><a href='${url.serviceContext}/api/node/content/${doc.nodeRef.storeRef.protocol}/${doc.nodeRef.storeRef.identifier}/${doc.nodeRef.id}/${doc.name?url}'>${doc.name}</a></#if>",

	</p>
	
</#list>
