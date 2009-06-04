<#import "node.lib.ftl" as nodeLib/>
[
<#list resultset as result>
<@nodeLib.nodeJSON result=result />
<#if result.doc.id != resultset?last.doc.id>,</#if>
</#list>
]
