from facepy import *

"""
Wraps facepy
"""

class UserInfo:
    def __init__(self):
        pass

    def __str__(self):
        return "this is going to contain all the text related to the user. search it."
        

class DirtyGraphAPI():
    def __init__(self, access_token):
        self.graph = GraphAPI(access_token)
        
        
## API usage:
if __name__ == '__main__':
    test_user = UserInfo()
    mystring = str(test_user) # search this
    print mystring 
    
