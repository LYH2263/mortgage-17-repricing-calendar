<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([])
const parse = (h) => {
  const input = JSON.parse(h.input_json || '{}')
  const result = JSON.parse(h.result_json || '{}')
  return {
    ...h,
    rate: input.annual_rate_used ?? input.annual_rate,
    hit: input.window_hit,
    monthly: result.monthly_payment,
    interest: result.total_interest,
  }
}
const hitLabel = (hit) => (hit === true ? '命中窗' : hit === false ? '窗外' : '—')
onMounted(async () => { items.value = (await getJSON('/api/history')).items.map(parse) })
</script>
<template><div class="page"><h1>试算记录</h1>
<p>记录钉选测算当时所用年利率，事后调整重定价窗不回写。</p>
<table>
  <tr><th>#</th><th>时间</th><th>所用年利率%</th><th>窗</th><th>月供</th><th>利息合计</th></tr>
  <tr v-for="h in items" :key="h.id">
    <td>#{{ h.id }}</td><td>{{ h.created_at }}</td><td>{{ h.rate }}</td><td>{{ hitLabel(h.hit) }}</td><td>{{ h.monthly }}</td><td>{{ h.interest }}</td>
  </tr>
</table>
</div></template>
