const webpack = require('webpack')

const definePlugin = new webpack.DefinePlugin({
  'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'development')
})

module.exports = {
  configureWebpack: {
    plugins: [definePlugin]
  }
}
