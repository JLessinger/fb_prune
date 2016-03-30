from pprint import pprint
from facepy import *
import argparse
import decimal
import logging
import json
import os
import sys

"""
Wraps facepy
"""

def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError

class UserInfo:
    def __init__(self,
                 uid,
                 access_token,
                 max_depth=2,
                 page_limit=25,
                 exclude_con=set([]),
                 suppress_w = False):
        self.id = uid
        self.access_token = access_token
        self.dirty_graph = DirtyGraphAPI(self.access_token, suppress_w)
        self.max_depth = max_depth
        self.page_limit = page_limit
        self.exclude_con = exclude_con
        self.suppress_w = suppress_w

    def as_json_obj(self, max_depth, page_limit, exclude_con):
        return self.dirty_graph.get_all_obj_data('me',
                                                 max_depth,
                                                 page_limit,
                                                 exclude_con)

    def __str__(self):
        return json.dumps(self.as_json_obj(self.max_depth, self.page_limit, self.exclude_con),
                          indent=2, sort_keys=True, default=decimal_default)
        

class DirtyGraphAPI():
    def __init__(self, access_token, page_limit=25, max_depth=2, suppress_w=False):
        self.graph = GraphAPI(access_token)
        self.page_limit = page_limit
        self.max_depth = max_depth
        self.suppress_w = suppress_w

    def get_raw_connections(self, path):
        #print 'getting connections of ' + path
        new_path = os.path.join(path, '?metadata=1')
        try:
            conns = self.graph.get(new_path)['metadata']['connections'].keys()
            print 'connections for {0}:'.format(path)
            pprint(conns, width=1)
            return conns
        except OAuthError as e:
            if not self.suppress_w:
                self.log_get_conn_error(e, "connections for " + path)
            return set([])

    def get_path_for_conn(self, path, con):
        return os.path.join(path, con)

    def gen_exhausted(self, gen):
        try:
            next_item = next(gen)
        except StopIteration:
            return True
        return False

    def log_get_conn_error(self, error, conn_path):
        sys.stderr.write('WARNING: {0}, cannot get {1}. Continuing...\n'
                         .format(type(error).__name__, conn_path))

    def get_node_paths_for_conn(self, path, con, max_depth, page_limit):
        con_path = self.get_path_for_conn(path, con)
        ids = []
        try:
            page_gen = self.graph.get(con_path, page=True, max_depth=max_depth, page_limit=page_limit)
            for page in page_gen:
                for el in page['data']:
                    ids.append(el['id'])
        except (OAuthError, FacebookError, UnicodeDecodeError) as e:
            if not self.suppress_w:
                self.log_get_conn_error(e, con_path)
        except KeyError as e:
            # this is not actually an error; just means last page.
            bad_key = e.args[0]
            assert bad_key == 'id'
            assert self.gen_exhausted(page_gen)
        return ids

    def get_connection_nodes_for_obj(self, path, con, max_search_depth, page_limit, exclude_con):
        return [self.get_all_obj_data(node_path,max_search_depth - 1,
                                      page_limit,
                                      exclude_con) \
                for node_path in self.get_node_paths_for_conn(path, con, \
                                                              max_depth=max_search_depth, page_limit=page_limit)]

    # expects path to single endpoint object
    def get_all_obj_fields(self, path):
        try:
            return self.graph.get(path)
        except OAuthError as e:
            if not self.suppress_w:
                self.log_get_conn_error(e, "fields of " + path)
            return {}

    # expects an endpoint that returns a single node (json object)
    def get_all_obj_data(self,
                         path,
                         max_search_depth,
                         page_limit,
                         exclude_con):
        if max_search_depth == 0:
            return {'[MAX DEPTH REACHED]' : '...'}
        else:
            raw_connections = self.get_raw_connections(path)
            connections = {
                con : self.get_connection_nodes_for_obj(path,
                                                       con,
                                                       max_search_depth,
                                                       page_limit,
                                                       exclude_con) \
                           for con in raw_connections if con not in exclude_con

                }
            assert len(exclude_con.intersection(connections.keys())) == 0
            return {'fields' : self.get_all_obj_fields(path), 'connections' : connections}

if __name__ == '__main__':
    excludes_default = set(['insights', # insights -> possible facepy bug: https://github.com/jgorset/facepy/issues/99
                            'friends' # slow; assume unnecessary
                            ])

    parser = argparse.ArgumentParser(description='get your dirty fb data')
    parser.add_argument('access_token', type=str, help='FB API access token')
    parser.add_argument('--debug', '-d', action='store_true', help='FB API debug info')
    parser.add_argument('--suppress-warnings', '-s', action='store_true')
    parser.add_argument('--max-depth', '-m', type=int, default=1, help='maximum depth of nested objects to produce')
    parser.add_argument('--page-limit', '-p', type=int, default=25,
                        help='maximum number of pages of a given connection to look through')
    parser.add_argument('--excludes', '-e', nargs='*', default = excludes_default,
                        help='names of connections to ignore')

    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    user = UserInfo('jonathan',
                    args.access_token,
                    max_depth=args.max_depth,
                    page_limit=args.page_limit,
                    exclude_con=args.excludes,
                    suppress_w=args.suppress_warnings)
    print str(user)




