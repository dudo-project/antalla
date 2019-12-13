const envConfigs = {
  development: {
    wsURL: 'ws://localhost:8765'
  },
  production: {
    wsURL: 'wss://stream.dudo.tech'
  }
}

const config = {}

module.exports = Object.assign(config, envConfigs[process.env.NODE_ENV]);
