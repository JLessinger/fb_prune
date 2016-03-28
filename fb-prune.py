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
        return self.dirty_graph.get_all('me/', max_depth)

    def __str__(self):
        return json.dumps(self.as_json_obj(3), indent=2, sort_keys=True)
        

class DirtyGraphAPI():
    def __init__(self, access_token):
        self.graph = GraphAPI(access_token)

    def get_all(self, path, max_search_depth):
        json_str = '{"__complex__": true, "real": 1, "imag": 2}'
        parsed = json.loads(json_str)
        return parsed
        
        
## API usage:
if __name__ == '__main__':
    user = UserInfo(100, 'abc')
    print str(user)

