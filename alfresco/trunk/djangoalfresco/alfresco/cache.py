#
# Copyright 2009 Optaros, Inc.
#
"""
Need to save things locally to reduce load on alfresco. 
This will happen with xml and images for the most part.

Idea, Save keys, timeouts in cache. This will allow us to invalidate the cache easily
"""
import os

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
    
class ImageCache(object):
    """
    Really not a cache, but i'm too lazy to change the name. 
    
    .get: looks through the alfresco images directory and tries to find the image. If it's not there it returns None
    .set: creates the file in the alfresco images directory.
    """
    file_root = os.path.join(settings.MEDIA_ROOT,'alfresco/images')
    image_url = settings.MEDIA_URL + 'alfresco/images/'
    
    def get(self, key, extension=None):
        """
        returns a url not a file
        """        
        if extension:
            file_location = os.path.join(self.file_root, '%s.%s' % (key, extension))
            if default_storage.exists(file_location):
                return self.image_url + key + '.' + extension
        else:
            d = dict([ (a.split('.')[0], a)   for a in default_storage.listdir(self.file_root)[1]])
            if d.has_key(key):
                return self.image_url + d[key]
        
        return None
    
    def set(self, key, extension, value, timeout=None):
        try:
            file_location = os.path.join(self.file_root, key + '.' + extension)
            if default_storage.exists(file_location):
                default_storage.delete(file_location)
            file_location = default_storage.save(file_location, ContentFile(value))
            value = self.image_url + key + '.' + extension
            return value
        except:
            return None

image_cache = ImageCache()
        
        