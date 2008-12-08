from django.db.models import Field
from django.forms.widgets import Input
from django.utils.safestring import mark_safe
from django.core import exceptions
from django.utils.translation import ugettext_lazy
from django.utils.encoding import smart_unicode

##########################
#######  Widgets  ########
##########################
class AlfrescoInput(Input):

    def __init__(self, attrs={}):
        super(AlfrescoInput, self).__init__(attrs={'class': 'alfrescoField'})           

    def render(self, name, value, attrs=None):
        html = super(AlfrescoInput, self).render(name, value, attrs) 
        return mark_safe(html + '&nbsp;<a class="alfresco_search_link" rel="#alfresco_search" onclick="javascript:alfresco_id_field=\'id_%s\'">Search</a>' % name)

class AlfrescoField(Field):
    def get_internal_type(self):
        return "CharField"

    def to_python(self, value):
        if isinstance(value, basestring):
            return value
        if value is None:
            if self.null:
                return value
            else:
                raise exceptions.ValidationError(
                    ugettext_lazy("This field cannot be null."))
        return smart_unicode(value)

    def formfield(self, **kwargs):
        defaults = {'widget': AlfrescoInput}
        defaults.update(kwargs)
        return super(AlfrescoField, self).formfield(**defaults)