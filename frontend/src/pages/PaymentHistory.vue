<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([])
onMounted(async () => { items.value = (await getJSON('/api/history')).items })
const parse = (s) => { try { return JSON.parse(s) } catch { return {} } }
</script>
<template><div class="page"><h1>试算记录</h1>
<p>已写入记录钉选当时所用年利率，事后修改重定价窗不会改写历史。</p>
<table>
  <tr v-for="h in items" :key="h.id">
    <td>#{{ h.id }}</td>
    <td>{{ h.created_at }}</td>
    <td>钉选年利率 {{ parse(h.input_json).annual_rate }}%</td>
    <td>月供 {{ parse(h.result_json).monthly_payment }}</td>
  </tr>
</table>
</div></template>
