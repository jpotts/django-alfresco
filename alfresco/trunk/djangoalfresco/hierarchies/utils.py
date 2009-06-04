#
# Copyright 2009 Optaros, Inc.
#
def slugify(slug):
    import re
    slug = slug.strip().lower()
    slug = re.sub(r'[^a-z0-9 ]', '', slug)
    slug = re.sub(r' +', '-', slug)
    return slug

def get_path_bits(path):
    return [bit.strip() for bit in path.strip().strip('/').split('/')]

def slugify_path(path):
    return '/%s' % '/'.join([slugify(bit) for bit in get_path_bits(path)])