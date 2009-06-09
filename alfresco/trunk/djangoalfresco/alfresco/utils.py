#
# Copyright 2009 Optaros, Inc.
#
import re

from xml.dom import minidom
from alfresco.settings import ALFRESCO_DEFAULT_USER, ALFRESCO_DEFAULT_USER_PASSWORD, ALFRESCO_EXTERNAL_USER_CACHE_TIME_OUT
from django.core.cache import cache

def create_search_string(get={}):
    values = []
    for key, value in get.items():
        if not value or key in ['page', 'order_by', 'page_size']:
            continue
        if key == 'q':
            if value.startswith('TEXT'):
                values.append(value)
            else:
                values.append('TEXT:%s' % value)
        else:
            values.append(value)
    return ' AND '.join(values).replace(' ', '%20')

def create_tag_search_string(get={}):
    values = []
    for key, value in get.items():
        if not value or key in ['page', 'order_by', 'page_size']:
            continue
        if key == 'q':
            if value.startswith('PATH'):
                values.append(value)
            else:                    
                values.append('PATH:"/cm:taggable/cm:%s/member"' % value)
        else:
            values.append(value)
    return ' AND '.join(values).replace(' ', '%20')

def clean_q(params):
    """
    This keeps the form and the pagination working.
    """
    name_re = re.compile('^@\\\{.*\}(?P<name>.*?):.*$')
    q_re = re.compile('TEXT:(?P<name>\w+)')
    params = params.copy()
    if params.has_key('q') and params['q'].startswith('TEXT'):
        name_list = params['q'].split(' AND ')
        for name in name_list:
            match = name_re.match(name)
            if match:
                params[match.groups()[0]] = name
        params['q'] = q_re.match(params['q']).groups()[0]
    return params


def make_get_urls(**kwargs):
    """
    Useful Helper to keep track of the get params.
    Use:
        'get_params' : make_get_urls(page=page, page_size=page_size, order_by=order_by)
    Template
        href="{{get_params.page}}page=1"
    html:
        href="?page_size=10&order_by=modified&page=1"
    """
    r = {}
    keys = kwargs.keys()
    for k in keys:
        n = {}
        for key, value in kwargs.items():
            if key != k and value:
                n[key] = value
        r[k] = '?' + '&'.join(['%s=%s' % (i, v) for i, v in n.items()])
        if len(r[k]) is not 1:
            r[k] += '&'
    return r

def get_constraints(xml, namespace, constraint, name):
    namespace = namespace.replace(':', '\:')
    values = []
    for element in xml.getElementsByTagName('constraints')[0].getElementsByTagName('constraint'):
        if element.getAttribute('name') == constraint:
            value_list = element.getElementsByTagName('parameter')[0].getElementsByTagName('value')
            for value in value_list:
                text = value.childNodes[0].data
                values.append(('@\{%s\}%s:"%s"' % (namespace,name,text),text),)
            break
    
    return values

def get_external_user_ticket():
    """
    For external sites that use django to serve content we don't want to have them get
    a ticket everytime. let's keep one around for awhile.
    """
    from alfresco.service import login, AlfrescoException
    KEY = 'alfresco.utils.get_external_user_ticket.ticket'
    ticket = cache.get(KEY)
    if not ticket:
        try:
            ticket = login(ALFRESCO_DEFAULT_USER, ALFRESCO_DEFAULT_USER_PASSWORD)
        except AlfrescoException:
            #No need to log, login does that.
            return None
        cache.set(KEY, ticket, ALFRESCO_EXTERNAL_USER_CACHE_TIME_OUT)
    return ticket

def generate_hex_key(*args):
    string_key = ':'.join([str(a) for a in args])
    try:
        #hashlib is 2.5, md5 is for 2.4
        import hashlib
    except ImportError:
            import md5
            return md5.new(string_key).hexdigest()
    else:
        return hashlib.md5(string_key).hexdigest()
    
#Taken from posixpath.py
def join(a, *p):
    """Join two or more pathname components, inserting '/' as needed"""
    path = a
    for b in p:
        if b.startswith('/'):
            path = b
        elif path == '' or path.endswith('/'):
            path +=  b
        else:
            path += '/' + b
    return path