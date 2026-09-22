<script setup>
import { ref } from 'vue'
import { postJSON } from '../api'
const principal = ref(800000)
const annual_rate = ref(4.2)
const months = ref(360)
const useStart = ref(false)
const start_month = ref(12)
const start_day = ref(1)
const out = ref(null)
const error = ref('')
const run = async () => {
  error.value = ''
  const body = { principal: principal.value, annual_rate: annual_rate.value, months: months.value, persist: true }
  if (useStart.value) { body.start_month = start_month.value; body.start_day = start_day.value }
  try { out.value = await postJSON('/api/schedule', body) } catch (e) { error.value = e.message }
}
</script>
<template><div class="page"><h1>等额本息试算</h1>
<label>本金 <input v-model.number="principal" /></label>
<label>年利率% <input v-model.number="annual_rate" /></label>
<label>月数 <input v-model.number="months" /></label>
<label><input type="checkbox" v-model="useStart" /> 按起息月日走重定价窗</label>
<template v-if="useStart">
  <label>起息月 <input type="number" v-model.number="start_month" min="1" max="12" /></label>
  <label>起息日 <input type="number" v-model.number="start_day" min="1" max="31" /></label>
</template>
<button @click="run">计算</button>
<p v-if="error" class="err">{{ error }}</p>
<template v-if="out">
  <p v-if="out.window_hit === null">未参与重定价窗（未填起息月日或规则停用），按请求年利率计。</p>
  <p v-else-if="out.window_hit">起息日落入重定价窗：<strong>命中窗</strong>，按窗内年利率计。</p>
  <p v-else>起息日在重定价窗外：<strong>未命中窗</strong>，按窗外年利率计。</p>
  <p>所用年利率 {{ out.annual_rate_used }}% · 月供 {{ out.monthly_payment }} · 利息合计 {{ out.total_interest }}</p>
</template>
</div></template>
<style scoped>
.err { color: #a33; font-weight: 700; }
</style>
