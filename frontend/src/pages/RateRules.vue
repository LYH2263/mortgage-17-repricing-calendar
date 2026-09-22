<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, postJSON, putJSON } from '../api'

const blank = { start_month: 11, start_day: 1, end_month: 2, end_day: 28, in_window_rate: 3.1, out_window_rate: 3.6, enabled: true }
const items = ref([])
const form = ref({ ...blank })
const editingId = ref(null)
const error = ref('')

const md = (m, d) => `${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`
const showErr = (e) => {
  try { error.value = JSON.parse(e.message).detail ?? e.message } catch { error.value = e.message }
}
const load = async () => { items.value = (await getJSON('/api/repricing/rules')).items }
const save = async () => {
  error.value = ''
  try {
    if (editingId.value) await putJSON(`/api/repricing/rules/${editingId.value}`, form.value)
    else await postJSON('/api/repricing/rules', form.value)
    cancel()
    await load()
  } catch (e) { showErr(e) }
}
const edit = (r) => {
  editingId.value = r.id
  const { id, created_at, updated_at, ...fields } = r
  form.value = { ...fields, enabled: !!r.enabled }
  error.value = ''
}
const cancel = () => { editingId.value = null; form.value = { ...blank } }
const disable = async (r) => {
  error.value = ''
  try { await postJSON(`/api/repricing/rules/${r.id}/disable`, {}); await load() } catch (e) { showErr(e) }
}
const enable = async (r) => {
  error.value = ''
  try { await putJSON(`/api/repricing/rules/${r.id}`, { ...r, enabled: true }); await load() } catch (e) { showErr(e) }
}
onMounted(load)
</script>

<template>
  <div class="page">
    <h1>起息日重定价窗</h1>
    <p>同一时刻只允许一条启用规则。起息月日落入窗内（窗可跨年）按窗内年利率计，否则按窗外年利率计。</p>

    <table>
      <tr><th>#</th><th>窗起</th><th>窗止</th><th>窗内年利率%</th><th>窗外年利率%</th><th>状态</th><th>操作</th></tr>
      <tr v-for="r in items" :key="r.id">
        <td>#{{ r.id }}</td>
        <td>{{ md(r.start_month, r.start_day) }}</td>
        <td>{{ md(r.end_month, r.end_day) }}</td>
        <td>{{ r.in_window_rate }}</td>
        <td>{{ r.out_window_rate }}</td>
        <td>{{ r.enabled ? '启用' : '停用' }}</td>
        <td>
          <button @click="edit(r)">编辑</button>
          <button v-if="r.enabled" @click="disable(r)">停用</button>
          <button v-else @click="enable(r)">启用</button>
        </td>
      </tr>
      <tr v-if="!items.length"><td colspan="7">暂无规则</td></tr>
    </table>

    <h2>{{ editingId ? `编辑规则 #${editingId}` : '新建规则' }}</h2>
    <div class="rule-form">
      <label>窗起 月 <input type="number" v-model.number="form.start_month" min="1" max="12" /></label>
      <label>日 <input type="number" v-model.number="form.start_day" min="1" max="31" /></label>
      <label>窗止 月 <input type="number" v-model.number="form.end_month" min="1" max="12" /></label>
      <label>日 <input type="number" v-model.number="form.end_day" min="1" max="31" /></label>
      <label>窗内年利率% <input type="number" step="0.01" v-model.number="form.in_window_rate" /></label>
      <label>窗外年利率% <input type="number" step="0.01" v-model.number="form.out_window_rate" /></label>
      <label><input type="checkbox" v-model="form.enabled" /> 启用</label>
      <button @click="save">{{ editingId ? '保存' : '创建' }}</button>
      <button v-if="editingId" @click="cancel">取消</button>
    </div>
    <p v-if="error" class="err">{{ error }}</p>
  </div>
</template>

<style scoped>
.rule-form { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; }
.rule-form input[type="number"] { width: 6rem; }
.err { color: #a33; font-weight: 700; }
</style>
