import config from './config'

export default class WsHandler {
  constructor() {
    this.socket = new WebSocket(config.wsURL)
  }

  send(action, data) {
    const message = { action, data };
    this.socket.send(JSON.stringify(message));
  }

  addEventListener(name, func) {
    if (name === 'message') {
      func = this._wrapOnMessage(func);
    }
    return this.socket.addEventListener(name, func);
  }

  _wrapOnMessage(func) {
    return (message) => {
      return func(JSON.parse(message.data), message);
    };
  }
}
