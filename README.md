# django-alfresco
Leverage the power and functionality of a robust rich content store (Alfresco) with agility and rapid application development on the front-end presentation tier powered by Django.

This was originally built for an Optaros client as a way to implement an Enterprise portal. Content is tagged, secured, and routed for approval in Alfresco. Django is used to build the front-end web site. Django requests (and caches) content objects from Alfresco via RESTful calls over HTTP.

Authentication is handled by making Alfresco the authority--if a user can successfully log in to Alfresco, they can automatically log in to the Django-powered site. Django requests an Alfresco ticket and keeps it with the Django user object, renewing it when needed. 
