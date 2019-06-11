import unittest
from unittest.mock import MagicMock, call

from antalla.actions import InsertAction, UpdateAction


class ActionsTest(unittest.TestCase):
    def setUp(self):
        self.mock_session = MagicMock()

    def test_insert_action(self):
        items = [1, 2, 3]
        action = InsertAction(items)
        self.assertEqual(action.execute(self.mock_session), 3)
        self.mock_session.add.assert_has_calls([call(1), call(2), call(3)])

    def test_update_action(self):
        model = MagicMock()
        results = [MagicMock(), MagicMock()]
        action = UpdateAction(model, {"name": "old_name"}, {"name": "new_name"})
        self.mock_session.query.return_value.filter_by.return_value = results
        self.assertEqual(action.execute(self.mock_session), 2)
        self.mock_session.query.assert_called_once_with(model)
        self.mock_session.query.return_value.filter_by.assert_called_once_with(name="old_name")
        for result in results:
            self.assertEqual(result.name, "new_name")

