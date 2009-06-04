 == ABOUT ==

This is the Optaros Alfresco-Django integration project. It includes three packages:

 - alfresco: This package contains the core integration code including a backend, manager, service, some basic objects, and a minimal set of URLs and views.
 - hierarchies: This package is used to map a set of hierarchies and associated categories to spaces in Alfresco. For example, you might have a 'blog' hierarchy that contains a category for each of your blog's channels. Each category can map to a "space" (folder) in Alfresco.
 - sample_site: This is a sample site showing crude blog functionality, feeds, search, tags, and static content.
 
The sample_site and hierarchies packages depend on the alfresco package.

 == COMPATIBILITY ==

This project has been tested with:
 Python 2.5
 Django 1.0.2_1
 Alfresco 3d Labs, Alfresco 3.0.1 Enterprise, and Alfresco 3.1 Enterprise
 MySQL 5.0.77

 == INSTALL ==

These instructions assume Django, Tomcat, Alfresco, and databases are already installed.

1. Create a local_settings.py file with the following values set appropriately for your environment:

# Local Django settings for djangoalfresco project.

DATABASE_ENGINE = 'mysql'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = 'django'             # Or path to database file if using sqlite3.
DATABASE_USER = 'django'             # Not used with sqlite3.
DATABASE_PASSWORD = 'django'         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

2. From the command-line, from within the project's root directory (the same directory in which this file appears), run syncdb:

python manage.py syncdb

When prompted to create a super user, answer no.

3. You have two choices for how to prepare Alfresco:

Option 1: Use Ant to create and deploy an AMP file and sample data bootstrap

a. Obtain the Alfresco MMT JAR either by downloading a pre-built JAR or building it yourself.
b. Create a file called build.properties using build.properties.sample as a guide. Edit the property values for your environment. The alfresco.war.path should point to a copy of your Alfresco WAR file.
c. Run "ant deploy-amp". Ant will use the Alfresco MMT to update the WAR with the Django web scripts and a bootstrap data ACP file. A backup of your original Alfresco WAR file will be created.
d. Start Tomcat. You should see a log entry similar to:
e. Go on to Step 4.

User:System INFO  [repo.module.ModuleServiceImpl] Installing module 'com.optaros.django' version 1.0.

Option 2: Deploy web scripts and sample data by hand

NOTE: The biggest drawback to this option is that the UUIDs of the objects may change when you import the sample site data and will therefore not match up with the data in the Django fixtures. If you don't care about the sample site, that's not a problem. If you want to see a working sample site, it is strongly recommended to use option 1. Otherwise, you'll have to change all of the Django objects to match the new UUIDs.

a. Deploy the web scripts in alfresco/webscripts. You can either copy the "com" directory and its children into the repository under Data Dictionary/Web Script Extensions or you can copy them to your deployed Alfresco web application under $TOMCAT_HOME/webapps/alfresco/WEB-INF/classes/alfresco/extension/templates/webscripts.
b. Start Tomcat. If Tomcat was already running, and you deployed to the Data Dictionary, go to http://localhost:8080/alfresco/service/ to refresh the list of web scripts.
c. Log in to Alfresco as an Administrator and navigate to Company Home.
d. Go to the Admin Control Panel, click Import, and specify the ACP file in sample-data/sample_site.acp.
e. Go on to Step 4.

4. Start the site by running the following:

python manage.py runserver

5. Browse the site: http://localhost:8000

If you have NOT changed your Alfresco admin login, Django will use the default "admin/admin" credentials to establish a ticket. It will also create a corresponding user in Django with the same user and password, and will mark the account as Django Superuser and Staff.

If you HAVE changed your password, or you have disabled the "admin" account, a login will be presented. Log in with a valid Alfresco username and password. A corresponding user entry in Django will be created. If the username is "admin" it will be marked as Superuser and Staff.

You can log out at any time by browsing to:

http://localhost:8000/alfresco/logout

6. Edit the Site entry in Django admin. Go to: http://localhost:8000/admin. Log in as an administrator. Edit the example Site entry. Change the domain name to "localhost:8000". If you don't do this, links in the blog feeds will not work.


   