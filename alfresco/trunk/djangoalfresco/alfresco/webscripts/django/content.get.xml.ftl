<?xml version="1.0" encoding="utf-8"?>
<django-objects version="1.0">
	<object pk="${doc.id}" model="alfresco.content">
		<field type="CharField" name="name"><#if doc.properties['name']?exists> ${doc.properties['name']}</#if></field>
    	<field type="CharField" name="space">${doc.parent.id}</field>
    	<field type="CharField" name="mimetype">${doc.properties.content.mimetype}</field>
		<field type="CharField" name="size">${doc.properties.content.size}</field>
		<field type="CharField" name="description"><#if doc.properties['description']?exists> ${doc.properties['description']}</#if></field>
		<field type="CharField" name="title"><#if doc.properties['title']?exists> ${doc.properties['title']}</#if></field>
		<field type="CharField" name="author"><#if doc.properties['author']?exists> ${doc.properties['author']}</#if></field>
		<field type="TextField" name="content"><![CDATA[<#if doc.properties.content.mimetype?substring(0,4) == 'text'>${doc.content}<#else><a href='${url.serviceContext}/api/node/content/${doc.nodeRef.storeRef.protocol}/${doc.nodeRef.storeRef.identifier}/${doc.nodeRef.id}/${doc.name?url}'>${doc.name}</a></#if>]]></field>
		<field type="DateField" name="created"><#if doc.properties['created']?exists>${doc.properties['created']?string("yyyy-MM-dd")}</#if></field>
		<field type="DateField" name="modified"><#if doc.properties['modified']?exists>${doc.properties['modified']?string("yyyy-MM-dd")}</#if></field>
		<field type="CharField" name="url">${url.serviceContext}/api/node/content/${doc.nodeRef.storeRef.protocol}/${doc.nodeRef.storeRef.identifier}/${doc.nodeRef.id}/${doc.name?url}</field>
	</object>
</django-objects>
