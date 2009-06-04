<#import "node.lib.ftl" as nodeLib/>
<?xml version="1.0" encoding="utf-8"?>
<django-objects version="1.0">
	<#list results as result>
	<@nodeLib.nodeXML result=result />
	</#list>
</django-objects>