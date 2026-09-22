<script setup>
import { ref } from 'vue'
import { postJSON } from '../api'
const principal = ref(800000)
const annual_rate = ref(4.9)
const months = ref(360)
const value_month = ref(null)
const value_day = ref(null)
const out = ref(null)
const errMsg = ref('')

const errText = (e) => {
  try { return JSON.parse(e.message).detail || e.message } catch { return e.message }
}

const run = async () => {
  out.value = null
  errMsg.value = ''
  const body = { principal: principal.value, annual_rate: annual_rate.value, months: months.value, persist: true }
  const m = Number(value_month.value)
  const d = Number(value_day.value)
  const hasM = value_month.value !== null && value_month.value !== '' && !Number.isNaN(m)
  const hasD = value_day.value !== null && value_day.value !== '' && !Number.isNaN(d)
  if (hasM !== hasD) { errMsg.value = '起息月与起息日必须同时填写或同时留空' ; return }
  if (hasM && hasD) {
    if (m < 1 || m > 12) { errMsg.value = '起息月须在 1-12' ; return }
    if (d < 1 || d > 31) { errMsg.value = '起息日须在 1-31' ; return }
    body.value_month = m
    body.value_day = d
  }
  try {
    out.value = await postJSON('/api/schedule', body)
  } catch (e) {
    errMsg.value = errText(e)
  }
}

const hitLabel = (v) => v === true ? '命中窗（窗内年利率）' : v === false ? '未命中窗（窗外年利率）' : '未参与定价（使用请求年利率）'
</script>
<template><div class="page"><h1>等额本息试算</h1>
<label>本金 <input v-model.number="principal" /></label>
<label>年利率% <input v-model.number="annual_rate" /></label>
<label>月数 <input v-model.number="months" /></label>
<label>起息月 <input v-model.number="value_month" type="number" min="1" max="12" placeholder="留空不参与" /></label>
<label>起息日 <input v-model.number="value_day" type="number" min="1" max="31" placeholder="留空不参与" /></label>
<button @click="run">计算</button>
<p v-if="errMsg" style="color:#b3261e">{{ errMsg }}</p>
<div v-if="out">
  <p>定价结果：{{ hitLabel(out.rate_window_hit) }}</p>
  <p>所用年利率 {{ out.applied_annual_rate }}%</p>
  <p>月供 {{ out.monthly_payment }} · 利息合计 {{ out.total_interest }}</p>
</div>
</div></template>
