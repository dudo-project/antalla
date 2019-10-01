import unittest

from antalla import db


class TransactionalTestCase(unittest.TestCase):
    def setUp(self):
        self.session = db.Session()
        self.session.commit = lambda: None
            
    def tearDown(self):
        self.session.rollback()
