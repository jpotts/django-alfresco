#
# Copyright 2009 Optaros, Inc.
#
from django.test import TestCase
from alfresco.models import Space,Content,StaticContent
from hierarchies.models import Hierarchy,Category
from alfresco import settings
from alfresco import service

class AlfrescoTestCase(TestCase):
    
    fixtures = ['initial_data.json']

    TEST_HIERARCHY_SLUG = 'blog'
    TEST_HIERARCHY_TITLE = 'Blog'

    def setUp(self):
        self.ticket = service.login(settings.ALFRESCO_DEFAULT_USER, settings.ALFRESCO_DEFAULT_USER_PASSWORD)
    
    def testSpaces(self):
        some_channel_space = Space.objects.all()[0]
        
        contents = None
        search_contents = None
        filter_contents = None
        
        try:
            contents = some_channel_space.contents.all(alf_ticket=self.ticket)
        except service.AlfrescoException, e:
            self.fail(str(e))
        
        try:
            search_contents = some_channel_space.contents.search(q=some_channel_space.q_path_directly_below(), sort_by='-modified', alf_ticket=self.ticket)
        except service.AlfrescoException, e:
            self.fail(str(e))
            
        try:
            filter_contents = some_channel_space.contents.filter(limit=2, order_by='-modified', alf_ticket=self.ticket)
        except service.AlfrescoException, e:
            self.fail(str(e))
        
        if search_contents and filter_contents:
            self.assertTrue(search_contents[0].id == filter_contents[0].id)
        
        if some_channel_space.category:
            response = self.client.get(some_channel_space.category.get_absolute_url())
            self.assertContains(response, "Some Channel")
            self.assertTemplateUsed(response, 'categories/detail.html')
      
    def testLogin(self):
        response = self.client.post('/alfresco/login/', {'username': 'admin', 'password': 'admin'})
        self.assert_(response.status_code is 200)
        self.assertFormError(response, 'form', 'next', 'This field is required.')
        
        response = self.client.post('/alfresco/login/', {'username': 'admin', 'password': 'admin', 'next' :'/'})
        self.assert_(response.status_code == 302)
        self.assertRedirects(response, '/')
        
    def testContent(self):
        ''' Test the Content object.'''
        
        TEST_CONTENT_ID = '0599e21d-d078-4911-a4a6-8ad5a7ae7f1d'        
        TEST_CONTENT_TITLE = 'Another piece of content'
        # retrieve a piece of content and check its props
        try:
            content = Content.objects.get(id=TEST_CONTENT_ID, alf_ticket=self.ticket)
        except service.AlfrescoException, e:
            self.fail(str(e))
        
        self.assertEquals(content.id, TEST_CONTENT_ID)
        self.assertEquals(content.name, 'test-2.html')
        self.assertEquals(content.title, TEST_CONTENT_TITLE)
        self.assertEquals(content.description, 'This is another piece of content for the Some Channel channel.')
        self.assertEquals(content.author, 'Jeff Potts')
        # tags aren't coming through on ACP export/import
                
        # open the content detail view    
        response = self.client.get(content.get_absolute_url())
        self.assertContains(response, TEST_CONTENT_TITLE)
        self.assertTemplateUsed(response, 'categories/content_detail.html')
        
        # test arbitrary content retrieval
        response = self.client.get('/alfresco/content/91d99a53-bd18-420a-8979-17a423bcf2d8/')
        self.assertContains(response, 'Some test content')
        self.assertTemplateUsed(response, 'alfresco/detail.html')
        
    def testStaticContent(self):
        ''' Test the StaticContent object.'''
        TEST_CONTENT_ID = 'e3663b57-1489-4cb6-be63-e7d65c4a266d'
        TEST_IMAGE_ID = '4f9b27e2-bf28-4e46-9e70-c8bd1e93d64a'
        
        # retrieve a piece of static content
        try:
            static_content = StaticContent.objects.get(doc_id=TEST_CONTENT_ID)
        except service.AlfrescoException, e:
            self.fail(str(e))
            
        self.assertEquals(static_content.description, 'Solutions navigation list')
        self.assertEquals(static_content.name, 'Solutions')
        self.assertEquals(static_content.slug, 'solutions')

        # open the static content via "static" url
        response = self.client.get(static_content.get_absolute_url())
        self.assertContains(response, 'Solutions navigation')
                    
        # retrieve a piece of static content
        try:
            image_content = StaticContent.objects.get(doc_id=TEST_IMAGE_ID)
        except service.AlfrescoException, e:
            self.fail(str(e))
            
        self.assertEquals(image_content.description, 'Image of the book cover')
        self.assertEquals(image_content.name, 'Alfresco Developer Guide Cover Image')
        self.assertEquals(image_content.slug, 'book-cover')
    
        # open the static content via "image" url
        response = self.client.get('/alfresco/image/%s' % image_content.slug)
        self.assertEquals(response.status_code, 302)
              
    def testHierarchy(self):
        '''Test the Hierarchy object.'''
        self.deleteTestHierarchy()
        self.assertEquals(Hierarchy.objects.all().count(), 0)
                
        blog_space = Space.objects.filter(name='Blog')[0]

        test_hierarchy = Hierarchy(name=self.TEST_HIERARCHY_TITLE, slug=self.TEST_HIERARCHY_SLUG, space=blog_space)
        test_hierarchy.save()
                
        self.assertEquals(test_hierarchy.get_templates()[0], 'hierarchies/%s/detail.html' % self.TEST_HIERARCHY_SLUG)
        self.assertEquals(test_hierarchy.get_templates()[1], 'hierarchies/detail.html')
        self.assertEquals(test_hierarchy.get_absolute_url(), '/%s/' % self.TEST_HIERARCHY_SLUG)
        
        response = self.client.get(test_hierarchy.get_absolute_url())
        self.assertContains(response, self.TEST_HIERARCHY_TITLE)
        self.assertTemplateUsed(response, 'hierarchies/detail.html')
        
        self.deleteTestHierarchy()    
    
    def deleteTestHierarchy(self):
        '''Delete the test hierarchy and all related objects'''
        blog_hierarchy = Hierarchy.objects.filter(name=self.TEST_HIERARCHY_TITLE)[0]
        blog_hierarchy.delete()        
         
    def testCategory(self):
        '''Test the Category object.'''
        SOCIAL_CATEGORY_TITLE = 'Social eCommerce'
        
        self.deleteTestHierarchy()
        self.assertEquals(Hierarchy.objects.all().count(), 0)
        self.assertEquals(Category.objects.all().count(), 0)
             
        blog_space = Space.objects.filter(name=self.TEST_HIERARCHY_TITLE)[0]
        
        test_hierarchy_filter = Hierarchy.objects.filter(name=self.TEST_HIERARCHY_TITLE)
        if test_hierarchy_filter.count() == 0:
            test_hierarchy = Hierarchy(name=self.TEST_HIERARCHY_TITLE, slug=self.TEST_HIERARCHY_SLUG, space=blog_space)
            test_hierarchy.save()
        else:
            test_hierarchy = test_hierarchy_filter[0]
                    
        ecommerce_space = Space.objects.filter(name='eCommerce')[0]
        social_space = Space.objects.filter(name='Social eCommerce')[0]
        plugins_space = Space.objects.filter(name='eCommerce Plugins')[0]
        
        hierarchy = Hierarchy.objects.filter(name=self.TEST_HIERARCHY_TITLE)[0]
                
        ecommerce_category = Category(hierarchy=hierarchy, name='eCommerce', slug='ecommerce', space=ecommerce_space)
        ecommerce_category.save()
        
        plugins_category = Category(hierarchy=hierarchy, parent=ecommerce_category, name='eCommerce Plugins', slug='ecommerce-plugins', space=plugins_space)
        plugins_category.save()
        
        social_category = Category(hierarchy=hierarchy, parent=ecommerce_category, name=SOCIAL_CATEGORY_TITLE, slug='social-ecommerce', space=social_space)
        social_category.save()
        
        # get_all_children
        self.assertEquals(len(ecommerce_category.get_all_children()), 2L)
        self.assertEquals(len(social_category.get_all_children()), 0)
        
        # get_top_content
        # TODO
        
        # get_templates
        self.assertEquals(plugins_category.get_templates()[0], 'categories/blog/ecommerce/ecommerce-plugins/detail.html')
        
        # breadcrumbs
        self.assertEquals(plugins_category.breadcrumbs()[0]['url'], '/blog/')
        self.assertEquals(plugins_category.breadcrumbs()[0]['name'], 'Blog')
        self.assertEquals(plugins_category.breadcrumbs()[1]['url'], '/blog/ecommerce/')
        self.assertEquals(plugins_category.breadcrumbs()[1]['name'], 'eCommerce')
                                                            
        # absolute URL, template used
        response = self.client.get(social_category.get_absolute_url())
        self.assertContains(response, SOCIAL_CATEGORY_TITLE)
        self.assertTemplateUsed(response, 'categories/detail.html')
