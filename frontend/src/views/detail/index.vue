<template>
  <div class="device-info">
    <div class="name">设备sn:{{ device_name }}</div>
    <div class="chart-wrap">
      <LineChart
        :data="cpuInfo"
        title="cpu"
        :displayKeys="['device_cpu_rate', 'idle_rate', 'pid_cpu_rate', 'system_rate', 'user_rate']"
      />
    </div>
    <div class="chart-wrap">
      <LineChart :data="memInfo" title="memInfo" :displayKeys="['freemem', 'pss', 'totalmem']" />
    </div>
    <div class="chart-wrap">
      <LineChart
        :data="fpsInfo"
        title="fpsInfo"
        :displayKeys="['fps', 'jank', 'pid_cpu_rate', 'system_rate', 'user_rate']"
      />
    </div>
  </div>
</template>

<script setup>
import { getCpuInfo, getMemInfo, getFpsInfo } from '@/service/apis'
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import LineChart from '@/components/lineChart.vue'

const route = useRoute()

const { device_name, other_field } = route.query

const cpuInfo = ref([
  {
    device_cpu_rate: 23,
    idle_rate: 23,
    pid_cpu_rate: 34,
    system_rate: 23,
    user_rate: 34,
    datetime: '2024-05-05',
  },
  {
    device_cpu_rate: 23,
    idle_rate: 23,
    pid_cpu_rate: 34,
    system_rate: 23,
    user_rate: 34,
    datetime: '2024-05-06',
  },
])

const memInfo = ref([
  {
    freemem: 23,
    pss: 23,
    totalmem: 34,
    datetime: '2024-05-05',
  },
  {
    freemem: 23,
    pss: 23,
    totalmem: 34,
    datetime: '2024-05-06',
  },
])

const fpsInfo = ref([
  {
    fps: 23,
    jank: 23,
    datetime: '2024-05-05',
  },
  {
    fps: 23,
    jank: 23,
    datetime: '2024-05-06',
  },
])

watch(
  () => [device_name, other_field],
  ([name, field]) => {
    if (name && field) {
      const data = {
        device_name: name,
        other_field: field,

        // device_name: 'S301YJTEST000006',
        // other_field: 'bb4ebaca-ae4d-41f8-8178-2956a06366a8',
      }

      getCpuInfo(data).then((res) => {
        console.log('get_cpu_info', res[0].details)
        cpuInfo.value = res[0].details
      })

      getMemInfo(data).then((res) => {
        console.log('getMemInfo', res[0].details)
        memInfo.value = res[0].details
      })

      getFpsInfo({
        ...data,
      }).then((res) => {
        console.log('getFpsInfo', res[0].details)
        fpsInfo.value = res[0].details
      })
    }
  },
  {
    immediate: true,
  },
)
</script>

<style scoped lang="less">
.chart-wrap {
  height: 400px;
  border: 1px solid #ccc;
  border-radius: 12px;
  margin-top: 40px;
}
</style>
