#
# Copyright 2009 Optaros, Inc.
#
from django import template
from alfresco.service import AlfrescoException

class AlfrescoTemplateNode(template.Node):
    """
    I really don't like this.
    """
    def render(self, context):
        try:
            return self.deliver(context)
        except AlfrescoException, a:
            if a.code is 1:
                user = template.Variable('user').resolve(context)
                ticket = user.default_user_login()
                if not ticket or context.get('alfresco_template_node_login_tried', False):
                    return '' 
                else:
                    context['alfresco_template_node_login_tried'] = True
                    context['user'] = user
                    try:
                        self.render(context)
                    except:
                        return ''
            else:
                return ''

    def deliver(self, context):
        """
        Override this function
        """
        pass
        
    def __iter__(self):
        yield self