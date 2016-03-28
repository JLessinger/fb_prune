from facepy import *
import json

"""
Wraps facepy
"""

class UserInfo:
    def __init__(self, uid, access_token):
        self.id = uid
        self.access_token = access_token
        self.dirty_graph = DirtyGraphAPI(self.access_token)

    def as_json_obj(self, max_depth):
        return self.dirty_graph.get_all_obj_data('me/', max_depth)

    def __str__(self):
        return json.dumps(self.as_json_obj(3), indent=2, sort_keys=True)
        

class DirtyGraphAPI():
    def __init__(self, access_token):
        self.graph = GraphAPI(access_token)

    def get_fields_for_obj(self, path):
        pass

    def get_connection_types(self, path):
        pass

    def get_connection_path(self, obj_path, con_type):
        pass

    def get_all_data_ids(self, path):
        pass
        # do paging

    # expects an endpoint that represents a list
    def get_all_list_data(self, path, max_search_depth):
        if max_search_depth == 0:
            return ['[MAX DEPTH REACHED]']
        else:
            pass
            # construct list via paging
            return [self.get_all_obj_data(self.path_of(data_id), max_search_depth - 1) \
                    for data_id in self.get_all_data_ids(path)]

    # expects an endpoint that returns a single node (json object)
    def get_all_obj_data(self, path, max_search_depth):
        if max_search_depth == 0:
            return {'[MAX DEPTH REACHED' : '...'}
        else:
            fields = self.get_fields_for_obj(path)
            connection_types = self.get_connection_types(path)
            connections = {type : self.get_all_list_data(self.get_connection_path(path, type), max_search_depth - 1) \
                           for type in connection_types}
            return {'fields' : fields, 'connections' : connections}
        
        
## API usage:
if __name__ == '__main__':
    user = UserInfo(100, 'abc')
    print str(user)

