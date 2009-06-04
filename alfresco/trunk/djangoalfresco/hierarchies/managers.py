#
# Copyright 2009 Optaros, Inc.
#
from django.db import models

class CategoryManager(models.Manager):
   def rootChildren(self, *args, **kwargs):
       return self.get_query_set().filter(parent=None, *args, **kwargs)