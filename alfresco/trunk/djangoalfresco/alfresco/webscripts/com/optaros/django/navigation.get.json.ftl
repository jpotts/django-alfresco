[
<#list nodes as node >
{	"id" : "${node.id}",
	"name" : "${node.name}",
  "path" : "${node.displayPath}",
  "qname" : "${node.qnamePath}",
  "nodeRef" : "${node.nodeRef}",
  "type": "${node.type}"
}
<#if node.id != nodes?last.id>,</#if>
</#list>
]
