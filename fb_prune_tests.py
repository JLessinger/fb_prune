from mock_graph_api import MockGraphAPI
from fb_prune import DirtyGraphAPI, UserInfo

import unittest

class TestDirtyGraph(unittest.TestCase):
    def setUp(self):
        excludes_default = set(['insights', # insights -> possible facepy bug: https://github.com/jgorset/facepy/issues/99
                        'friends',
                        'request_history'
                        ])
        self.dg = DirtyGraphAPI(MockGraphAPI, 'fake')
        self.user = UserInfo(0, 'abc', 1, 25, exclude_con=excludes_default, graph=self.dg)

    def test_1(self):
        print str(self.user)