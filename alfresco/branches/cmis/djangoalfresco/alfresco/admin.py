from django.contrib import admin
from alfresco.models import Node

class NodeAdmin(admin.ModelAdmin):
    class Media:
        js = (
              'admin/js/jquery.treeview.js',
        )
        css = {
            "all": ("admin/css/jquery.treeview.css",)
        }

admin.site.register(Node, NodeAdmin)