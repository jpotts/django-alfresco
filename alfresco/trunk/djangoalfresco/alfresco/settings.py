#
# Copyright 2009 Optaros, Inc.
#
from django.conf import settings
from django.utils.datastructures import SortedDict

ALFRESCO_URL =  getattr(settings, 'ALFRESCO_URL', 'http://localhost:8080/')
ALFRESCO_SERVICE_URL = ALFRESCO_URL + 'alfresco/service/'
ALFRESCO_SPACE_STORE_URL =   ALFRESCO_URL +'alfresco/download/attach/workspace/SpacesStore/'
ALFRESCO_CONTENT_SUB_URL = ALFRESCO_URL + 'alfresco/service/news/upload'

# Set this to the Alfresco ID of the root space from which to build the space navigation
# Setting this to none will generate a tree based on the entire Alfresco spacestore
ALFRESCO_SPACE_NAVIGATION_ROOT_ID =  getattr(settings, 'ALFRESCO_SPACE_NAVIGATION_ROOT_ID', None)
ALFRESCO_SPACE_NAVIGATION_ROOT_CACHE_TIMEOUT =  getattr(settings, 'ALFRESCO_SPACE_NAVIGATION_ROOT_CACHE_TIMEOUT', 86400)

# CACHE
ALFRESO_CACHE_FILE_TIMEOUT = getattr(settings, 'ALFRESO_CACHE_FILE_TIMEOUT', 1800)

ALFRESCO_EXCEPTION_CODES = {
    1: 'Your alfresco ticket has timed out or you have insufficient privileges to view this folder. Please login again.',
    2: 'Alfresco is currently not running or Django is pointed at an invalid instance.',
    3: 'The Request made to Alfresco was incorrectly formated',
    4: 'The Alfresco url requested does not exist'}

ALFRESCO_DEFAULT_USER = getattr(settings, 'ALFRESCO_DEFAULT_USER', 'admin')
ALFRESCO_DEFAULT_USER_PASSWORD = getattr(settings, 'ALFRESCO_DEFAULT_USER_PASSWORD', 'admin')

ALFRESCO_AUTO_LOGIN_ATTEMPTS = getattr(settings, 'ALFRESCO_AUTO_LOGIN_ATTEMPTS', 3)

#Thumbnailing defaults from : /alfresco-trunk/HEAD/root/projects/repository/config/alfresco/thumbnail-service-context.xml
ALFRESCO_THUMBNAIL_SIZES = ('medium', 'imgpreview', 'avatar', 'doclib',)
ALFRESCO_LOCAL_THUMBNAIL_URL = getattr(settings, 'ALFRESCO_LOCAL_THUMBNAIL_URL', settings.MEDIA_URL +'alfresco/images/thumbnails/')
ALFRESCO_LOCAL_THUMBNAIL_ROOT = getattr(settings, 'ALFRESCO_LOCAL_THUMBNAIL_ROOT', settings.MEDIA_ROOT +'alfresco/images/thumbnails/')

ALFRESCO_EXTERNAL_USER_CACHE_TIME_OUT = getattr(settings, 'ALFRESCO_EXTERNAL_USER_CACHE_TIME_OUT', 21600) #6 hours
ALFRESCO_GENERIC_SEARCH_CACHE_TIMEOUT = getattr(settings, 'ALFRESCO_GENERIC_SEARCH_CACHE_TIMEOUT', 3600) #1 hour