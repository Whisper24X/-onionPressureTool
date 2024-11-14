<template>
  <div ref="echartRef" class="chart-dom"></div>
</template>

<script setup>
import { onMounted, ref, shallowRef, watch, onBeforeMount, nextTick } from 'vue'
import echarts from '@/utils/echarts.js'
import { useElementSize } from '@vueuse/core'

const props = defineProps({
  title: String,
  data: {
    type: Array,
    default: () => [],
  },
  displayKeys: {
    type: Array,
    default: () => [],
  },
})

const echartRef = ref()
const echartInstance = shallowRef()
const options = ref()
const setOptions = (data) => {
  let temp = {}
  let xAxisData = []
  const dataMap = data.reduce((obj, item) => {
    xAxisData.push(item.datetime)
    props.displayKeys.forEach((v) => {
      if (!obj[v]) {
        obj[v] = []
      }
      obj[v].push(item[v])
    })
    return obj
  }, {})
  temp = {
    title: {
      text: props.title || '标题',
    },
    tooltip: {
      trigger: 'axis',
    },
    legend: {
      data: props.displayKeys,
    },
    grid: {
      left: '3%',
      right: '4%',
      containLabel: true,
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 10,
      },
      {
        start: 0,
        end: 10,
      },
    ],
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: xAxisData,
    },
    yAxis: {
      type: 'value',
    },
    series: props.displayKeys.map((v) => {
      return {
        name: v,
        data: dataMap[v],
        type: 'line',
        smooth: true,
      }
    }),
  }

  options.value = temp

  nextTick(() => {
    echartInstance.value.setOption(options.value)
    echartInstance.value.resize()
  })
}

// 自适应父容器大小
const { width, height } = useElementSize(echartRef)
watch([width, height], () => {
  if (echartInstance.value && width && height) {
    echartInstance.value.resize()
  }
})

watch(
  () => props.data,
  (newVal) => {
    setOptions(newVal)
  },
  {
    // immediate: true,
  },
)

onMounted(() => {
  echartInstance.value = echarts.init(echartRef.value)
})

onBeforeMount(() => {
  echartInstance.value?.dispose()
})
</script>

<style scoped>
.chart-dom {
  width: 100%;
  height: 100%;
}
</style>
