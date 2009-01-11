from django.test import TestCase
from alfresco.models import Space
from alfresco import settings
from alfresco import service

class AlfrescoTestCase(TestCase):
    
    fixtures = ['initial_data.json']
    
    def setUp(self):
        self.ticket = service.login(settings.ALFRESCO_DEFAULT_USER, settings.ALFRESCO_DEFAULT_USER_PASSWORD)
    
    def testSpaces(self):
        newsworthy = Space.objects.all()[0]
        
        contents= None
        search_contents = None
        filter_contents = None
        
        try:
            contents = newsworthy.contents.all(alf_ticket=self.ticket)
        except service.AlfrescoException, e:
            self.fail(str(e))
        
        try:
            search_contents = newsworthy.contents.search(q=newsworthy.q_path_directly_below(), sort_by='-modified', alf_ticket=self.ticket)
        except service.AlfrescoException, e:
            self.fail(str(e))
            
        try:
            filter_contents = newsworthy.contents.filter(limit=2, order_by='-modified', alf_ticket=self.ticket)
        except service.AlfrescoException, e:
            self.fail(str(e))
        
        if search_contents and filter_contents:
            self.assertTrue(search_contents[0].id == filter_contents[0].id)
        
        if newsworthy.category:
            response = self.client.get(newsworthy.category.get_absolute_url())
            self.assertContains(response, "Newsworthy At NMG")
            self.assertTemplateUsed(response, 'categories/news/the-paper/detail.html')
    
    def testLogin(self):
        response = self.client.post('/alfresco/login/', {'username': 'admin', 'password': 'admin'})
        self.assert_(response.status_code is 200)
        self.assertFormError(response, 'form', 'next', 'This field is required.')
        
        response = self.client.post('/alfresco/login/', {'username': 'admin', 'password': 'admin', 'next' :'/'})
        self.assert_(response.status_code == 302)
        self.assertRedirects(response, '/')