from django.contrib import admin
from alfresco.models import Space, StaticContent

class SpaceAdmin(admin.ModelAdmin):
    class Media:
        js = (
              'admin/js/jquery.treeview.js',
        )
        css = {
            "all": ("admin/css/jquery.treeview.css",)
        }

class ContentAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ['name']

        
admin.site.register(Space, SpaceAdmin)
admin.site.register(StaticContent, ContentAdmin)