<template>
  <div id="app">
    <Header />
    <DepthChart />
  </div>
</template>

<script>
import DepthChart from './components/DepthChart.vue'
import Header from './components/Header.vue'

export default {
  name: 'app',
  components: {
    DepthChart,
    Header,
  }
}
</script>

<style>
#app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
}
</style>
