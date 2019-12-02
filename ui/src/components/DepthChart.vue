<template>
  <b-container>
    <h1>Market Depth Chart</h1>

    <div class="selection">
      <b-form-row>
        <b-col cols="4">
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
            value-field="original_name"
            text-field="original_name"
            :options="getMarkets()"
            ></b-form-select>
        </b-col>
      </b-form-row>
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
    }
  },

  methods: {
    findExchange(exchangeId) {
      return this.exchanges.find(exchange => exchange.id === exchangeId)
    },
    getMarkets() {
      if (!this.selectedExchange) {
        return []
      }
      return this.findExchange(this.selectedExchange).markets
    },
    onExchangeChange(value) {
      const exchange = this.findExchange(value)
      this.selectedMarket = exchange.markets[0].original_name
    }
  },

  mounted() {
    this.ws.addEventListener('open', () => {
      this.ws.send('list-exchanges')
    })
    this.ws.addEventListener('message', (payload) => {
      if (payload.action === 'exchanges') {
        this.exchanges = payload.data
        this.selectedExchange = this.exchanges[0].id
        this.selectedMarket = this.exchanges[0].markets[0].original_name
      }
    })
  }
}
</script>

<style scoped>
</style>
