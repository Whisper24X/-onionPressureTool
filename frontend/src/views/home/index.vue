<template>
  <div class="list-wrap">
    <ElCard class="card" v-for="(item, index) in deviceLists" :key="item.device_id + index">
      <div class="img-wrap">
        <img
          src="https://fp.yangcong345.com/onion-extension/ee-7019d075e6642eef2f6adb619d44217b.png"
          alt=""
        />
      </div>
      <div class="info">
        <p>设备SN：{{ item.device_id }}</p>
        <p>设备型号：{{ item.model }}</p>
        <p>设备系统：android{{ item.android_version }}</p>
        <p>运行内存：{{ item.device_ram }} GB</p>
        <p>运行端口：{{ item.tcp_port || '--' }}</p>
      </div>
      <div class="actions">
        <div class="btn" @click="start(item)">开始运行</div>
        <div class="btn" @click="stop(item)">停止运行</div>
      </div>
      <!-- <div class="detail" @click="toDtail({ device_name: item.device_id, other_field: 'xxx' })">
        查看性能运行数据
      </div> -->
      <div :class="['tag', { online: item.device_status === 1 }]"></div>
    </ElCard>
  </div>

  <div class="histroy-list">
    <el-table :data="histroyList" style="width: 100%" border :max-height="500">
      <el-table-column prop="device_name" label="设备SN" width="180" />
      <el-table-column prop="device_id" label="" width="180" />
      <el-table-column prop="model" label="设备型号" />
      <el-table-column prop="other_field" label="设备id" />
      <!-- <el-table-column prop="uuid" label="uuid" /> -->
      <el-table-column prop="created_at" label="created_at" />
      <el-table-column prop="act" label="操作">
        <template #default="scope">
          <el-button text @click="toDtail(scope.row)"> 参考性能报告 </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { deviceHistroyList, deviceList, deviceStart, deviceStop } from '@/service/apis'

import { ElCard, ElMessage, ElTable, ElTableColumn, ElButton } from 'element-plus'

import { onMounted, ref, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const deviceLists = ref([
  {
    device_id: 'device_id',
    tcp_port: 'tcp_port',
    android_version: '3',
    device_ram: '434',
    status: '连接成功',
    model: 'model',
    device_status: 1,
  },
])

const histroyList = ref([
  {
    created_at: '2024-11-06 17:20:49',
    device_id: 96,
    device_name: 'host.docker.internal:58665',
    model: '未知',
    other_field: 96,
    uuid: 'fdfdfdfd',
  },
])

const start = (item) => {
  console.log(item)
  deviceStart({
    deviceId: item.device_id,
    tcpPort: item.tcp_port,
  }).then((res) => {
    console.log('start', res)
    ElMessage.success('操作成功')
  })
}

const stop = (item) => {
  deviceStop({
    deviceId: item.device_id,
    tcpPort: item.tcp_port,
  }).then((res) => {
    console.log('stop', res)
    ElMessage.success('操作成功')
  })
}

const toDtail = (row) => {
  console.log(row)
  const newUrl = router.resolve({
    path: '/detail',
    query: {
      device_name: row.device_name,
      other_field: row.other_field,
    },
  })
  window.open(newUrl.href, '_blank')
}

const getDeviceList = () => {
  deviceList().then((res) => {
    console.log('deviceList', res)
    deviceLists.value = res
  })
}

let timer
const startTimer = () => {
  timer = setInterval(() => {
    getDeviceList()
  }, 5000)
}

onBeforeUnmount(() => {
  clearInterval(timer)
})

onMounted(() => {
  getDeviceList()
  deviceHistroyList().then((res) => {
    console.log('deviceStart', res)
    histroyList.value = res
  })
  startTimer()
})
</script>

<style scoped lang="less">
@keyframes fadeOut {
  0% {
    opacity: 1;
  }
  100% {
    opacity: 0;
  }
}
.list-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
}
.card {
  width: 300px;
  :deep(.el-card__body) {
    position: relative;
  }
  .tag {
    position: absolute;
    top: 10px;
    right: 10px;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background-color: #ccc;
    &.online {
      background-color: #27c027;
      animation: fadeOut 1.5s ease-in-out forwards infinite;
    }
  }
  .img-wrap {
    text-align: center;
    > img {
      width: 100px;
    }
  }
  .actions {
    display: flex;
    align-items: center;
    border-top: 1px solid #eee;
    padding-top: 16px;
    margin-top: 12px;
    > .btn {
      flex-grow: 1;
      cursor: pointer;
      text-align: center;
      line-height: 100%;
      &:hover {
        color: #409eff;
      }
      &:first-child {
        border-right: 1px solid #eee;
      }
    }
  }
  .detail {
    border-top: 1px solid #eee;
    padding-top: 12px;
    text-align: center;
    cursor: pointer;
    &:hover {
      color: #409eff;
    }
  }
}

.histroy-list {
  margin-top: 40px;
}
</style>
