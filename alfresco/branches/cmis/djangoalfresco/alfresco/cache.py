"""
Need to save things locally to reduce load on alfresco. 
This will happen with xml and images for the most part.

Idea, Save keys, timeouts in cache. This will allow us to invalidate the cache easily
"""
import os

from django.core.cache.backends.locmem import CacheClass
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings

from alfresco.settings import ALFRESO_CACHE_FILE_TIMEOUT

class AlfrescoCache(CacheClass):
    """
    Base class that made more sense when the ImageCache was actually a cache.
    """
    file_root = os.path.join(settings.MEDIA_ROOT,'alfresco/files')
    
    def __init__(self, params):
        CacheClass.__init__(self, None, params)
        try:
            os.makedirs(self.file_root)
        except:
            pass

class FileCache(AlfrescoCache):
    """
    Holds a key value pair for a content_id and it's file location. 
    
    Used heavily for saving the contents of a space locally for a period of time.
    
    .get: if the key exists it returns an xml file, else it returns none
    .set: creates the file in the alfresco file directory.
    """
    def __init__(self, params):
        params['timeout'] = ALFRESO_CACHE_FILE_TIMEOUT
        AlfrescoCache.__init__(self, params)
    
    def get(self, key, force=False):
        """
        returns a file
        """
        value = super(AlfrescoCache, self).get(key)
        if not value and force:
            value = os.path.join(self.file_root, key)
        if value:
            try:
                file = default_storage.open(value, 'r')
            except IOError:
                return None
            xml = file.read()
            file.close()
            return xml
        else:
            return None

    def set(self, key, value, timeout=None):
        """
        Value needs to be a file.
        
        Value needs to xml
        """
        file_name = os.path.join(self.file_root, key)
        if default_storage.exists(file_name):
            default_storage.delete(file_name)
        file_name = default_storage.save(file_name, ContentFile(value))
        super(AlfrescoCache, self).set(key, file_name, timeout)
    
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

file_cache = FileCache({}) 
image_cache = ImageCache()
        
        