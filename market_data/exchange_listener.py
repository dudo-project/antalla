from .base_factory import BaseFactory


class ExchangeListener(BaseFactory):
    def __init__(self, exchange, on_event):
        self.exchange = exchange
        self.on_event = on_event

    async def listen(self):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()

