from urlparse import urlparse, parse_qs
import os.path
import re
from inflection import singularize
from pprint import pprint


class NoSuchPathException(Exception):
    def __init__(self, path=None, resolved_from=None):
        self.path = path
        self.resolved_from = None

    def __str__(self):
        return repr(self)

    def __repr__(self):
        s = self.resolved_from + '->' + ' ' if self.resolved_from else ''
        return 'Exception: no ' + s + self.path


class MockGraphAPI():
    def __init__(self, access_token):
        pass # no real permissions
        self._aliases = {} # path -> id
        self._id_map = {} # id -> obj
        self._aliases['me'] = '0'

    def get(self, path, page=False, retry=3, **options):
        """

        :param path:
        :param page:
        :param retry: not yet supported
        :param options: not yet supported
        :return: if page=True, a page generator
                otherwise a json object (dictionary)
        """
        if page:
            return self._get_mock_page_gen(path)
        else:
            return self._get_mock_obj(path)

    def _get_mock_page_gen(self, path):
        path_str, params = self._parse_strip_req(path)
        lst_data_type = os.path.basename(path_str)
        possible_types = ['photos', 'feed', 'albums']
        if lst_data_type in possible_types:
            for i in xrange(3):
                data = []
                for j in xrange(2):
                    try:
                        # don't need actual object here, just partial one containing id
                        id = str(100 * (1 + possible_types.index(lst_data_type)) + 10 * i + j)
                        data.append({'id' : id})
                    except NoSuchPathException as e:
                        data.append(e)
                yield {'data' : data,
                       'paging' : {'previous' : 'whatever',
                                   'next' : 'whatever'}
                       }
            yield {'data' : []}

    def _get_mock_obj(self, path):
        path_str, params = self._parse_strip_req(path)

        try:
            path_str = self._aliases[path_str] # see if path_str is an alias
        except KeyError:
            pass # no alias for path; try resolving directly from it
        if self._get_cached_obj(path_str):
            return self._get_cached_obj(path_str)
        try:
            return self._resolve_obj_from_path(path_str, params)
        except NoSuchPathException as e:
            raise NoSuchPathException(path_str, e.path)


    def _parse_strip_req(self, path):
        """

        :param path:
        :return: tuple with stripped path and query params
        """
        parse_res = urlparse(path)
        params = parse_qs(parse_res.query)
        return (parse_res.path.strip('/'), params)

    def _get_meta(self, params, field_names, connection_types, type):
        """

        :param params: parsed parameters from query
        :param field_names: names of fields to give the object being requested
        :param connection_types: connection keys to give object
        :return: dictionary with metadata only
        """
        if 'metadata' in params and '1' in params['metadata']:
            return {'metadata' :
                        {'fields' :
                            [{'name' : field_name, 'decription' : 'whatever'} for field_name in field_names],
                         'connections' :
                            {connection_type : connection_type + 'url' for connection_type in connection_types},
                         'type' : type
                        }
                    }
        return {}

    def _get_cached_obj(self, path):
        """

        :param path: a path (including an id) to an obj
        :return: the obj or None
        """
        try:
            return self._id_map[path]
        except KeyError:
            try:
                return self._id_map[self._aliases[path]]
            except KeyError:
                return None

    def _set_cached_obj(self, path, id, obj):
        """

        :param path: unique path to assign to object
        :param id: unique id to assign to obj
        :param obj: object to assign to this path and id
        :return: dictionary elements assigning object to this path
        """
        # only one instance per id
        if id in self._id_map:
            assert self._id_map[id] is obj
        else:
            obj['id'] = id
            self._id_map[id] = obj
        if path in self._aliases:
            # don't reassign path
            assert self._aliases[path] == id
        else:
            self._aliases[path] = id


    def _resolve_obj_from_path(self, path_str, params):
        """

        :param path_str: stripped (no extra slashes)
        :return: new obj
        """
        obj = {}
        if path_str == '0':
            obj['name'] = 'jonathan'
            self._set_cached_obj(path_str, '0', obj) # add proper fields to obj and assign path and id globally to it
            obj.update(self._get_meta(params, ['name', 'id', 'birthday'], ['photos', 'feed', 'albums'], 'user'))
            return obj
        m = re.search('[0|me]/(photos|albums|feed)([0-9]+)$', path_str)
        if m:
            type = singularize(m.group(1))
            id = m.group(2)
            if int(id) < 100:
                raise NoSuchPathException(path_str)
            obj['type'] = type

            self._set_cached_obj(path_str, str(id), obj)
            if type == 'photo':
                fields = ['id', 'created_time']
                connections = ['comments', 'likes']
            elif type == 'album':
                fields = ['id', 'cover_photo']
                connections = ['comments', 'photos']
            elif type == 'feed':
                fields = ['id', 'message', 'story']
                connections = ['comments', 'attachments']
            obj.update(self._get_meta(params, fields, connections, type))
            return obj
        raise NoSuchPathException(path_str)


if __name__ == '__main__':
    m = MockGraphAPI('access')
    pprint([p for p in m.get('0/photos', page=True)])
    pprint(m.get('0?metadata=1'))
