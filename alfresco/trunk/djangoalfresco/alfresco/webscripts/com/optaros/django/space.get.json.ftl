<#import "node.lib.ftl" as nodeLib/>
[
<#list results as result>
<@nodeLib.nodeJSON result=result />
<#if result.doc.id != results?last.doc.id>,</#if>
</#list>
]
