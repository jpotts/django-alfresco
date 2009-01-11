import logging.config
import logging
import os
import inspect 

from django.conf import settings

class LogWrapper(object):
    def __init__(self):
        file_name= settings.LOGGING
        if file_name is  None:
            return
        try:
            fp= file(file_name, 'r')
            logging.config.fileConfig(fp)
        except :
            # we search in the module maybe we have 
            # only a file name
            try :
                modules = globals()
                module_path= os.path.dirname(modules['__file__'])
                fp= file(module_path+'/'+file_name, 'r')
                logging.config.fileConfig(fp)
            except Exception, e:
                print 'ERROR: Could not configure logging'
    
    def __getattr__(self, name):
        log_name = 'nmg'
        try:
            frame = inspect.currentframe().f_back
            st = frame.f_code.co_filename
            
            if st.find('djangoalfresco') > -1:
                st = st[st.rfind('djangoalfresco')+15:]
                st = st[:st.find('/')]
                log_name = 'nmg.' + st
        except:
            pass
        return getattr(logging.getLogger(log_name), name)

logger = LogWrapper()




 
