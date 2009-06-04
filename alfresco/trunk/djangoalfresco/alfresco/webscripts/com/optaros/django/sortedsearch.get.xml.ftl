<#import "node.lib.ftl" as nodeLib/>
<?xml version="1.0" encoding="utf-8"?>
<search-results>
	<params>
		<value name="q">${q}</value>
		<value name="sort_by">${sort_by}</value>
		<value name="start_index">${start_index}</value>
		<value name="stop_index">${stop_index}</value>
		<value name="num_results">${num_results}</value>
		<value name="page">${page}</value>
		<value name="page_size">${page_size}</value>
		<value name="num_pages">${num_pages}</value>
	</params>
	<django-objects version="1.0">
		<#list resultset as result>
		<@nodeLib.nodeXML result=result />
		</#list>
	</django-objects>
</search-results>
