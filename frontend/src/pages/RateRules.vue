<script setup>
import { onMounted, reactive, ref } from 'vue'
import { getJSON, postJSON } from '../api'

const items = ref([])
const errMsg = ref('')
const editingId = ref(null)

const blank = () => ({ start_month: 12, start_day: 1, end_month: 2, end_day: 28, in_rate: 3.6, out_rate: 4.2, enabled: false })
const form = reactive(blank())

const load = async () => { items.value = (await getJSON('/api/rate-window-rules')).items }
onMounted(load)

const md = (m, d) => `${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`

const errText = (e) => {
  try { return JSON.parse(e.message).detail || e.message } catch { return e.message }
}

const validate = () => {
  for (const [label, m, d] of [['窗起', form.start_month, form.start_day], ['窗止', form.end_month, form.end_day]]) {
    if (!Number.isInteger(m) || !Number.isInteger(d)) return `${label}月日需同时填写整数`
    if (m < 1 || m > 12) return `${label}月份须在 1-12`
    if (d < 1 || d > 31) return `${label}日期须在 1-31`
  }
  return ''
}

const resetForm = () => {
  Object.assign(form, blank())
  editingId.value = null
  errMsg.value = ''
}

const submit = async () => {
  errMsg.value = validate()
  if (errMsg.value) return
  try {
    const path = editingId.value ? `/api/rate-window-rules/${editingId.value}` : '/api/rate-window-rules'
    await postJSON(path, { ...form })
    resetForm()
    await load()
  } catch (e) {
    errMsg.value = errText(e)
  }
}

const edit = (r) => {
  errMsg.value = ''
  editingId.value = r.id
  Object.assign(form, {
    start_month: r.start_month, start_day: r.start_day,
    end_month: r.end_month, end_day: r.end_day,
    in_rate: r.in_rate, out_rate: r.out_rate, enabled: r.enabled,
  })
}

const disable = async (r) => {
  errMsg.value = ''
  try {
    await postJSON(`/api/rate-window-rules/${r.id}/disable`)
    if (editingId.value === r.id) resetForm()
    await load()
  } catch (e) {
    errMsg.value = errText(e)
  }
}
</script>

<template>
  <div class="page">
    <h1>起息日重定价窗</h1>
    <p>默认等额本息：月利率 = 年利率 / 12 / 100。同一时刻仅允许一条启用规则；窗以月日表示，可跨年（如 12-01 ～ 02-28），两端含。</p>
    <p v-if="errMsg" style="color:#b3261e">{{ errMsg }}</p>

    <table>
      <tr><th>ID</th><th>窗起</th><th>窗止</th><th>窗内年利率%</th><th>窗外年利率%</th><th>状态</th><th>操作</th></tr>
      <tr v-for="r in items" :key="r.id">
        <td>#{{ r.id }}</td>
        <td>{{ md(r.start_month, r.start_day) }}</td>
        <td>{{ md(r.end_month, r.end_day) }}</td>
        <td>{{ r.in_rate }}</td>
        <td>{{ r.out_rate }}</td>
        <td>{{ r.enabled ? '启用中' : '已停用' }}</td>
        <td>
          <button @click="edit(r)">编辑</button>
          <button v-if="r.enabled" @click="disable(r)">停用</button>
        </td>
      </tr>
    </table>

    <h2>{{ editingId ? `编辑规则 #${editingId}` : '新建规则' }}</h2>
    <div>
      <label>窗起月 <input v-model.number="form.start_month" type="number" min="1" max="12" /></label>
      <label>窗起日 <input v-model.number="form.start_day" type="number" min="1" max="31" /></label>
      <label>窗止月 <input v-model.number="form.end_month" type="number" min="1" max="12" /></label>
      <label>窗止日 <input v-model.number="form.end_day" type="number" min="1" max="31" /></label>
    </div>
    <div>
      <label>窗内年利率% <input v-model.number="form.in_rate" type="number" min="0" step="0.01" /></label>
      <label>窗外年利率% <input v-model.number="form.out_rate" type="number" min="0" step="0.01" /></label>
      <label>启用 <input v-model="form.enabled" type="checkbox" /></label>
    </div>
    <button @click="submit">{{ editingId ? '保存修改' : '创建' }}</button>
    <button v-if="editingId" @click="resetForm">取消</button>
  </div>
</template>
