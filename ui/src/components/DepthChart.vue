<template>
  <b-container>
    <h1>Market Depth Chart</h1>

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
        <div class="graph" v-else>
          <p>Some nice plot</p>
        </div>
      </b-row>
    </div>
    <div class="text-center" v-else>
      <b-spinner label="Spinning"></b-spinner>
    </div>

  </b-container>
</template>

<script>
import WsHandler from '../ws-handler'

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
    subscribe() {
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
      this.selectedExchange = this.exchanges[0].id
      this.selectedMarket = this.exchanges[0].markets[0].name
    },
    setDepthData(depthData) {
      if (this.subscription &&
          this.subscription.exchange === depthData.exchange &&
          this.subscription.buy_sym === depthData.buy_sym &&
          this.subscription.sell_sym === depthData.sell_sym) {
        this.depthData = depthData
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
</style>
