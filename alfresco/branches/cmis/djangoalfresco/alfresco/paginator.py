from alfresco.service import SearchWebScript

class AlfrescoSearchPage(object):
    def __init__(self, object_list, number, paginator, start_index, end_index):
        self.object_list = object_list
        self.number = number
        self.paginator = paginator
        self.start_index = start_index
        self.end_index = end_index

    def __repr__(self):
        return '<Page %s of %s>' % (self.number, self.paginator.num_pages)

    def has_next(self):
        return self.number < self.paginator.num_pages

    def has_previous(self):
        return self.number > 1

    def has_other_pages(self):
        return self.has_previous() or self.has_next()

    def next_page_number(self):
        return self.number + 1

    def previous_page_number(self):
        return self.number - 1


class AlfrescoSearchPaginator(object):
    """
    Very different from the Django Paginator.
    
    TODO: Document and use when we make the switch to 3.0
    """
    def __init__(self, *args, **kwargs):
        result_params, object_list = {}, []
        if kwargs.has_key('q') and kwargs['q']:
            s = SearchWebScript()
            result_params, object_list = s.paginate(*args, **kwargs)
        self.num_pages = int(result_params.get('num_pages', 0))
        self.num_results = int(result_params.get('num_results', 0))
        self.page_size = int(result_params.get('page_size', 10))
        self.q = result_params.get('q','')
        self.sort_by = result_params.get('sort_by', '-title')
        
        self.page = AlfrescoSearchPage(object_list, int(result_params.get('page',1)), \
                                       self, int(result_params.get('start_index',0)), int(result_params.get('stop_index',0)))
        
    def pages(self):
        return range(1, self.num_pages+1)
    
    def per_page(self):
        return self.page_size