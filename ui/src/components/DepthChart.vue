<template>
  <b-container>
    <div class="selection">
      <b-form-row>
        <b-col offset="2" cols="4">
          <b-form-select
            v-model="selectedExchange"
            value-field="id"
            text-field="name"
            @change="onExchangeChange($event)"
            :options="exchanges"
            ></b-form-select>
        </b-col>

        <b-col cols="4">
          <b-form-select
            v-model="selectedMarket"
            value-field="name"
            text-field="name"
            @change="onMarketChange($event)"
            :options="getMarkets()"
            ></b-form-select>
        </b-col>
      </b-form-row>
    </div>

    <div class="content" v-if="depthData">
      <b-row align-h="center">
        <b-alert v-if="depthData.size === 0"
          variant="warning" show>Not enough data to show, try another market
        </b-alert>
        <div id="depth-chart" v-else></div>
      </b-row>
    </div>
    <div class="text-center" v-else>
      <b-spinner label="Spinning"></b-spinner>
    </div>

  </b-container>
</template>

<script>
import WsHandler from '../ws-handler'
import Plotly from 'plotly.js-basic-dist'

const colors = {
  bids: '#5c6d70',
  asks: '#e88873'
}

export default {
  name: 'DepthChart',
  data() {
    return {
      ws: new WsHandler(),
      exchanges: [],
      selectedExchange: null,
      selectedMarket: null,
      running: false,
      depthData: null,
      subscription: null,
      graphDrawn: false,
    }
  },

  methods: {
    findExchange(exchangeId) {
      return this.exchanges.find(exchange => exchange.id === exchangeId)
    },
    findMarket(exchange, name) {
      return exchange.markets.find(market => market.name === name)
    },
    getMarkets() {
      if (!this.selectedExchange) {
        return []
      }
      return this.findExchange(this.selectedExchange).markets
    },
    onExchangeChange(value) {
      const exchange = this.findExchange(value)
      this.selectedMarket = exchange.markets[0].name
      this.subscribe()
    },
    onMarketChange() {
      this.subscribe()
    },
    makeSinglePlotData(orderType) {
      const key = orderType === 'bids' ? 'buy' : 'sell'
      const x = this.depthData[`${key}_price`]
      const y = this.depthData[`${key}_quantity`]
      const color = colors[orderType]
      const capitalizedOrderType = orderType[0].toUpperCase() + orderType.slice(1)
      return {
        x: x,
        y: y,
        name: `${capitalizedOrderType}`,
        fill: 'tozeroy',
        fillcolor: color,
        hoveron: 'fills+points',
        hoverinfo: 'name+x+y',
        hovermode: 'closest',
        line: {
          color: color
        }
      }
    },
    drawGraph() {
      if (this.depthData.size === 0) {
        return
      }
      // const funcName = this.graphDrawn ? 'update' : 'plot'
      const layout = {
        title: 'Depth chart',
        xaxis: {
          autorange: true,
          title: `Price Level (${this.depthData.sell_sym})`
        },
        yaxis: {
          autorange: true,
          title: `Quantity (${this.depthData.buy_sym})`
        }
      }
      const data = [this.makeSinglePlotData('bids'), this.makeSinglePlotData('asks')]
      if (this.graphDrawn) {
        Plotly.react('depth-chart', data, layout)
      } else {
        Plotly.plot('depth-chart', data, layout)
      }
      this.graphDrawn = true
    },
    subscribe() {
      if (this.graphDrawn) {
        Plotly.purge('depth-chart')
        this.graphDrawn = false
      }
      this.depthData = null
      this.subscription = null
      const exchange = this.findExchange(this.selectedExchange)
      if (!exchange) {
        return
      }
      const market = this.findMarket(exchange, this.selectedMarket)
      if (!market) {
        return
      }
      const [buySym, sellSym] = market.name.split('/')
      const data = {
        exchange: exchange.name,
        buy_sym: buySym,
        sell_sym: sellSym
      }
      this.subscription = data
      this.ws.send('subscribe-depth', data)
    },
    run() {
      if (this.running) {
        return
      }
      this.running = true
      this.subscribe()
    },
    initializeData(exchanges) {
      this.exchanges = exchanges
      for (const exchange of this.exchanges) {
        exchange.markets.sort((a, b) => a.name > b.name)
      }
      const exchange = exchanges.find(v => v.name === 'binance')
      this.selectedExchange = exchange.id
      this.selectedMarket = exchange.markets[0].name
    },
    setDepthData(depthData) {
      if (this.subscription &&
          this.subscription.exchange === depthData.exchange &&
          this.subscription.buy_sym === depthData.buy_sym &&
          this.subscription.sell_sym === depthData.sell_sym) {
        this.depthData = depthData
        this.$nextTick(() => this.drawGraph())
      }
    }
  },

  mounted() {
    this.ws.addEventListener('open', () => {
      this.ws.send('list-exchanges')
    })
    this.ws.addEventListener('message', (payload) => {
      if (payload.action === 'exchanges') {
        this.initializeData(payload.data)
        this.run()
      } else if (payload.action === 'depth') {
        this.setDepthData(payload.data)
      }
    })
  }
}

</script>

<style scoped>
.selection {
  margin: 2em 0;
}
#depth-chart {
  width: 90%;
}
</style>
