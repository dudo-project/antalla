import asyncio
import unittest
from unittest.mock import MagicMock


from antalla.orchestrator import Orchestrator
from antalla.exchange_listener import ExchangeListener
from antalla import models


@ExchangeListener.register("dummy")
class DummyListener(ExchangeListener):
    def __init__(self, exchange, on_event):
        super().__init__(exchange, on_event)
        self.mock_action = MagicMock()
        self.mock_action.execute.return_value = 2
        self.mock_stop = MagicMock()

    async def listen(self):
        self.on_event([self.mock_action, self.mock_action])

    def stop(self):
        self.mock_stop()



class OrchestratorTest(unittest.TestCase):
    def setUp(self):
        self.mock_session = MagicMock()
        self.dummy_exchange = models.Exchange(id=1337, name="dummy")
        query_exchange_ret = "query.return_value.filter_by.return_value.one.return_value"
        self.mock_session.configure_mock(**{query_exchange_ret: self.dummy_exchange})
        self.orchestrator = Orchestrator(["dummy"], session=self.mock_session, commit_interval=3)

    def test_listeners_instanciation(self):
        self.assertEqual(len(self.orchestrator.exchange_listeners), 1)
        self.assertIsInstance(self.dummy_listener, DummyListener)

    def test_start(self):
        asyncio.get_event_loop().run_until_complete(self.orchestrator.start())
        self.dummy_listener.mock_action.execute.assert_called_with(self.mock_session)
        self.assertEqual(self.dummy_listener.mock_action.execute.call_count, 2)

    def test_stop(self):
        self.orchestrator.stop()
        self.dummy_listener.mock_stop.assert_called_once()

    def test_periodic_commit(self):
        self.orchestrator._on_event([self.dummy_listener.mock_action])
        self.mock_session.commit.assert_not_called()
        self.orchestrator._on_event([self.dummy_listener.mock_action])
        self.mock_session.commit.assert_called_once()

    @property
    def dummy_listener(self):
        return self.orchestrator.exchange_listeners[0]

