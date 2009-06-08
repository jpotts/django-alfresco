#
# Copyright 2009 Optaros, Inc.
#
from django.db import models
from django.core import serializers
from django.core.urlresolvers import reverse
from django.core.cache import cache

from hierarchies import utils
from hierarchies.managers import CategoryManager

from alfresco.models import Space

class Hierarchy(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(help_text='A "Slug" is a unique URL-friendly title for an object.')
    order = models.PositiveIntegerField(default=0, editable=False)
    image = models.ImageField(upload_to='hierarchy/images/%m/%d/%Y/',  blank=True, null=True,)
    space = models.OneToOneField(Space, blank=True, null=True,)
    
    class Meta:
        verbose_name_plural = 'Hierarchies'
        ordering = ["order"]

    def __unicode__(self):
        return u'%s' % self.name
    
    def get_absolute_url(self):
        return reverse('hierarchy_detail',args=[self.slug])

    def get_parent_categories(self):
        return self.categories.filter(parent=None)
    
class Category(models.Model):
    hierarchy = models.ForeignKey('Hierarchy', blank=True, null=True, help_text="Must be explicitly selected if there is no parent category.", related_name='categories')
    parent = models.ForeignKey('self', blank=True, null=True, related_name='child',
        help_text="If not defined, this will be a top-level category in the given hierarchy.")
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    slug_path = models.CharField(max_length=300, blank=True, editable=False)
    
    top_stories = models.PositiveIntegerField(default=5)
    more_stories = models.PositiveIntegerField(default=10)
    
    cache = models.PositiveIntegerField(help_text="number of minutes you wish to cache the all xml for", default=15)
    #Header Image for the category
    image = models.ImageField(upload_to='category/images/%m/%d/%Y/',  blank=True, null=True,)

    order = models.PositiveIntegerField(default=0, editable=False)
    space = models.OneToOneField(Space, blank=True, null=True,)
    
    objects = CategoryManager()
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ["order"]
    
    def __unicode__(self):
        return u'/%s/' % (self.slug_path)
    
    def get_absolute_url(self):
        return reverse('category_detail',args=[self.slug_path])

    def save(self):
        if not self.hierarchy:
            self.hierarchy = self.parent.hierarchy
                
        if not self.slug:
            self.slug = utils.slugify(self.name)
            
        super(Category, self).save()
   
        self.refresh_paths()
        
    def _recurse_for_parents(self, cat_obj):
        p_list = []
        if cat_obj.parent_id:
            p = cat_obj.parent
            p_list.append(p)
            if p != self:
                more = self._recurse_for_parents(p)
                p_list.extend(more)
        if cat_obj == self and p_list:
            p_list.reverse()
        return p_list

    def refresh_paths(self, force=False):
        """
        Determines this Category's path by looking at its name and
        the paths of its parents. If it's changed, it's saved.
        """
        if self.parent_id is None:
            slug_path = '%s/%s' % (self.hierarchy.slug, self.slug)
        else:
            slug_path = '%s/%s' % (self.parent.slug_path, self.slug)
        if force or slug_path != self.slug_path:
            self.slug_path = slug_path
            self.save()
        
        for child in self.child.all():
            child.refresh_paths()
    
    
    def _flatten(self, L):
        """
        Taken from a python newsgroup post
        """
        if type(L) != type([]): return [L]
        if L == []: return L
        return self._flatten(L[0]) + self._flatten(L[1:])

    def _recurse_for_children(self, node):
        children = []
        children.append(node)
        for child in node.child.all():
            if child != self:
                children_list = self._recurse_for_children(child)
                children.append(children_list)
        return children

    def get_all_children(self):
        """
        Gets a list of all of the children categories.
        """
        children_list = self._recurse_for_children(self)
        flat_list = self._flatten(children_list[1:])
        return flat_list
            
    def get_top_content(self):
        #key = '__'.join([self._meta.app_label, self._meta.module_name, str(self.id)])
        key = str(self.space_id)
        xml = cache.get(key)
        if not xml:
            return []
        return [d.object for d in serializers.deserialize('xml', xml)]

    def set_top_content(self, xml):
        key = '__'.join([self._meta.app_label, self._meta.module_name, str(self.id)])
        file_cache.set(key, xml)
        
    def breadcrumbs(self):
        """
        Gets the breadcrumb trail for a given category. 
        """
        bcs = []
        cat = self
        while(1):
            bcs.append({"url": cat.get_absolute_url(), 'name' : cat.name})
            if cat.parent:
                cat = cat.parent
            else:
                bcs.append({"url": cat.hierarchy.get_absolute_url(), 'name' : cat.hierarchy.name})
                break;
        bcs.reverse()
        return bcs
    
    def get_rss(self):
        """
        Returns a string to assist with building RSS urls to the category top stories
        """
        return 'categories/' + self.slug_path
        