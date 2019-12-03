Integrating Exchanges
=====================


*antalla* tries to make it easy to integrate with new exchanges.
A couple of already implemented exchanges can be found in the
`antalla/exchange_listeners`_ directory.
We currently offer a ``WebsocketListener`` base class which allows to easily connect to exchanges
using a websocket interface.

The constructor must have the following signature and call its
parent as shown.

.. code-block:: python

    def __init__(self,
                 exchange,
                 on_event,
                 # all arguments below should have a default value
                 markets=LIST_OF_MARKETS,
                 ws_url=WEBSOCKET_URL,
                 session=db.session,
                 event_type="orders"):
        super().__init__(exchange, on_event, markets, ws_url, session=session, event_type=event_type)

The following two methods must be implemented to
integrate with a new exchange.

.. code-block:: python

    async def _setup_connection(self, websocket)

    def _parse_message(self, message)

``_setup_connection`` should take care of sending all the necessary messages
to the websocket server to subscribe to all the markets in the markets list
passed in the constructor and the events passed in ``event_type``, or all events
if nothing has been passed. ``self._log_event(market, "connect", event_type)``
should be called for each market subscribed.

``_parse_message`` must take a raw JSON message and return a list of `actions`_
to perform. For example, if a new order is received, ``_parse_message`` will
most likely return an ``InsertAction`` with a single `Order`_. It is the job
of the ``ExchangeListener`` to transform orders received into `Order`_ models.

Here is a minimal example of a custom exchange listener.


.. code-block:: python

    import websockets

    from antalla import actions
    from antalla import db
    from antalla import models
    from antalla.websocket_listener import WebsocketListener
    from antalla.exchange_listener import ExchangeListener

    WS_URL = "ws://example.com/ws"
    MARKETS = ["ETHBTC"]

    @ExchangeListener.register("dummy")
    class DummyListener(WebsocketListener):
        def __init__(self,
                    exchange,
                    on_event,
                    session=db.session,
                    markets=MARKETS,
                    ws_url=WS_URL,
                    event_type=None):
            super().__init__(exchange, on_event, markets, ws_url, session=session, event_type=event_type)

        async def _setup_connection(self, websocket):
            subscription_data = {
              "action": "subscribe",
              "markets": self.markets,
              "event": self.event_type
            }
            await websocket.send(json.dumps(subscription_data))
            for market in self.markets:
                self._log_event(market, "connect", self.event_type)

        def _parse_order(self, payload):
            # TODO: transform the payload in an Order
            # order = models.Order(...)
            return order

        def _parse_message(self, message):
            payload = json.loads(message["payload"])
            if payload["action"] == self.event_type:
                order = self._parse_order(payload)
                return [actions.InsertAction([order])]
            return []


.. _`antalla/exchange_listeners`: https://github.com/samwerner/antalla/tree/master/antalla/exchange_listeners
.. _`actions`: https://github.com/samwerner/antalla/tree/master/antalla/actions.py
.. _`Order`: https://github.com/samwerner/antalla/blob/master/antalla/models.py#L77