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

class DirtyGraphError(Exception):
    def __init__(self, fb_api_exc, message):
        self.fb_api_exc = fb_api_exc
        self.message = 'WARNING: {0}, cannot get {1}.'\
            .format(type(fb_api_exc).__name__, message)

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return self.message

class FieldsError(DirtyGraphError):
    def __init__(self, fb_api_exc, path):
        super(FieldsError, self).__init__(fb_api_exc, 'fields of ' + path)

class ConnectionTypeError(DirtyGraphError):
    def __init__(self, fb_api_exc, path):
        super(ConnectionTypeError, self).__init__(fb_api_exc, 'connections for ' + path)

class ConnectionNodeError(DirtyGraphError):
    def __init__(self, fb_api_exc, path):
        super(ConnectionNodeError, self).__init__(fb_api_exc, path)

class MaxDepthException(Exception):
    def __init__(self):
        super(MaxDepthException, self).__init__()

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return '[MAX DEPTH REACHED]'

class UserInfo:
    def __init__(self,
                 uid,
                 access_token,
                 max_depth=2,
                 page_limit=25,
                 exclude_con=set([]),
                 underlying_graph=None):
        self._id = uid
        self._access_token = access_token
        if underlying_graph is None:
            self._dirty_graph = DirtyGraphAPI(self._access_token)
        self._max_depth = max_depth
        self._page_limit = page_limit
        self._exclude_con = exclude_con

    def _as_json_obj(self, max_depth, page_limit, exclude_con):
        return self._dirty_graph.get_all_obj_data('me',
                                                 [],
                                                 max_depth,
                                                 page_limit,
                                                 exclude_con)

    def __str__(self):
        return json.dumps(self._as_json_obj(self._max_depth, self._page_limit, self._exclude_con),
                          indent=2, sort_keys=True, default=_encode_default)


class CursorMissingError(DirtyGraphError):
    def __init__(self, cursorkey):
        self._cursorkey = cursorkey

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return '[CURSOR {0} MISSING]'.format(self._cursorkey)

class DirtyGraphAPI():
    def __init__(self, access_token, page_limit=25, max_depth=2, underlying_class=GraphAPI):
        self._graph = underlying_class(access_token)
        self._page_limit = page_limit
        self._max_depth = max_depth

    def _get_page_gen(self, path, retry, **options):
        for p in self._graph.get(path, True, retry, **options):
            try:
                cursors = p['paging']['cursors']
                b = cursors['before']
                a = cursors['after']
            except KeyError as e:
                # if cursors is not defined, then neither are a or b
                # this is fine, define them here.
                # if cursors is defined, then it should contain before and after
                #   or neither before or after.
                assert e.args[0] in ['paging', 'cursors'] or \
                       ('before' in cursors == 'after' in cursors)
                a = CursorMissingError('after')
                b = CursorMissingError('before')
            range = '{0} -> {1}'.format(b, a)
            sys.stderr.write('dirty graph page {0} for {1}\n'.format(range, path))
            yield p

    def get(self, path='', page=False, retry=3, **options):
        if page:
            sys.stderr.write('connections for {0}:\n'.format(path))
            return self._get_page_gen(path, retry, options)
        else:
            sys.stderr.write('dirty graph getting {0}\n'.format(path))
            return self._graph.get(path, False, retry, **options)

    def get_page_data_gen(self, path='', retry=3, **options):
        try:
            page_gen = self._get_page_gen(path, retry, **options)
            for page in page_gen:
                for el in page['data']:
                    sys.stderr.write('getting connection node path {0} for object at {1}\n'.format(el['id'], path))
                    yield el['id']
        except KeyError as e:
            # this is not actually an error; just means last page.
            bad_key = e.args[0]
            assert bad_key == 'id'
            assert self._gen_exhausted(page_gen)

    def _get_connection_types(self, path):
        new_path = os.path.join(path, '?metadata=1')
        try:
            conns = self.get(new_path)['metadata']['connections'].keys()
            pprint(conns, width=1, stream=sys.stderr)
            return conns
        except OAuthError as e:
            raise ConnectionTypeError(e, path)

    def _get_path_for_conn(self, path, con):
        return os.path.join(path, con)

    def _gen_exhausted(self, gen):
        try:
            next(gen)
        except StopIteration:
            return True
        return False

    def _get_node_paths_for_conn(self, path, con, page_limit):
        con_path = self._get_path_for_conn(path, con)
        try:
            data_gen = self.get_page_data_gen(con_path, page_limit=page_limit)
            return [el for el in data_gen]
        except (OAuthError, FacebookError, UnicodeDecodeError) as e:
            raise ConnectionNodeError(e, con_path)

    def _get_connection_nodes_for_obj(self, path, prev_path_trace, con, max_search_depth, page_limit, exclude_con):
        node_paths_for_conn = self._get_node_paths_for_conn(path,
                                                           con,
                                                           page_limit=page_limit)
        return [self.get_all_obj_data(node_path,
                                      prev_path_trace + [(con, path)],
                                      max_search_depth - 1,
                                      page_limit,
                                      exclude_con) \
                for node_path in node_paths_for_conn]

    def _construct_conns_for_obj(self,
                                path,
                                prev_path_trace,
                                max_search_depth,
                                page_limit,
                                connection_types, exclude_con):
        connections = {}
        for con_type in connection_types:
            if con_type not in exclude_con:
                try:
                    conn_nodes = self._get_connection_nodes_for_obj(path,
                                                                   prev_path_trace,
                                                                   con_type,
                                                                   max_search_depth,
                                                                   page_limit,
                                                                   exclude_con)
                    connections[con_type] = conn_nodes
                except ConnectionNodeError as cn:
                    connections[con_type] = cn
        # if we successfully got the connection types, make sure to exclude the right ones
        assert len(exclude_con.intersection(connections.keys())) == 0
        return connections

    def _construct_obj(self, path, prev_path_trace, max_search_depth, page_limit, exclude_con):
        try:
            # first get fields
            fields = self._get_all_obj_fields(path)
        except FieldsError as f:
            # couldn't get fields for this object; record this by storing (printable) error in object
            fields = f
        # now recur into connections, storing errors if they occur
        try:
            connection_types = self._get_connection_types(path)
            connections = self._construct_conns_for_obj(path,
                                                       prev_path_trace,
                                                       max_search_depth,
                                                       page_limit,
                                                       connection_types,
                                                       exclude_con)
            # successfully gets connections for this object (path)
        except ConnectionTypeError as ct:
            connections = ct
            # name keys to define sort order for display
        return {'0path_trace:' : prev_path_trace,
                '1fields' : fields,
                '2connections' : connections}



    # expects path to single endpoint object
    def _get_all_obj_fields(self, path):
        try:
            return self.get(path)
        except OAuthError as e:
            raise FieldsError(e, path)

    # expects an endpoint that returns a single node (json object)
    def get_all_obj_data(self, path, prev_path_trace, max_search_depth, page_limit, exclude_con):
        if max_search_depth == 0:
            return MaxDepthException()
        else:
            return self._construct_obj(path, prev_path_trace, max_search_depth, page_limit, exclude_con)

def _encode_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    if isinstance(obj, DirtyGraphError):
        return str(obj)
    if isinstance(obj, Exception):
        return str(obj)
    raise TypeError

if __name__ == '__main__':
    excludes_default = set(['insights', # insights -> possible facepy bug: https://github.com/jgorset/facepy/issues/99
                            'friends',
                            'request_history'
                            ])

    parser = argparse.ArgumentParser(description='get your dirty fb data')
    parser.add_argument('access_token', type=str, help='FB API access token')
    parser.add_argument('--debug', '-d', action='store_true', default=False, help='FB API debug info')
    parser.add_argument('--max-depth', '-m', type=int, default=1,
                        help='maximum depth of nested objects to produce. default=1')
    parser.add_argument('--page-limit', '-p', type=int, default=25,
                        help='maximum number of pages of a given connection to look through. default=25',)
    parser.add_argument('--excludes', '-e', nargs='*', default = excludes_default,
                        help='names of connections to ignore. default = ' + str(excludes_default))

    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    user = UserInfo('jonathan',
                    args.access_token,
                    max_depth=args.max_depth,
                    page_limit=args.page_limit,
                    exclude_con=set(args.excludes))
    print str(user)




