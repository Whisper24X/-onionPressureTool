<template>
  <div class="report-container">
    <ElTable :data="reportList" style="width: 100%" row-key="report_id">
      <ElTableColumn type="expand">
        <template #default="props">
          <div v-if="props.row.details">
            <p class="time">测试完成时间：{{ props.row.details.time }}</p>
            <ElTable :data="props.row.details.testList" border class="detail-table">
              <ElTableColumn prop="type" label="用例名称" />

              <ElTableColumn prop="result" label="测试结果" width="100">
                <template #default="scope">
                  <ElTag :type="scope.row.result === '测试成功' ? 'success' : 'info'">
                    {{ scope.row.result }}
                  </ElTag>
                </template>
              </ElTableColumn>
              <ElTableColumn prop="detail" label="测试日志">
                <template #default="scope">
                  <div class="log-content">
                    <pre>{{ scope.row.detail }}</pre>
                  </div>
                </template>
              </ElTableColumn>
            </ElTable>
          </div>
        </template>
      </ElTableColumn>

      <ElTableColumn prop="report_id" label="报告ID" />
      <ElTableColumn prop="sn" label="设备SN" />
      <ElTableColumn prop="created_at" label="报告生成时间" />
    </ElTable>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getReportList } from '@/service/apis'
import { ElTable, ElTableColumn, ElTag } from 'element-plus'
import dayjs from 'dayjs'

const reportList = ref([])

const formatDate = (dateStr) => {
  if (!dateStr) return '--'
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm:ss')
}

// 获取报告列表
const fetchReportList = async () => {
  try {
    const res = await getReportList()
    reportList.value = res.map((item) => {
      return {
        ...item,
        created_at: formatDate(item.created_at),
        details: JSON.parse(item.details),
        expanded: false,
        loading: false,
      }
    })
  } catch (error) {
    console.error('获取报告列表失败：', error)
  }
}

onMounted(() => {
  fetchReportList()
})
</script>

<style scoped lang="less">
.report-container {
  padding: 20px;
}

.time {
  padding-left: 20px;
  padding-top: 10px;
}
.detail-table {
  margin: 10px 20px 20px;

  .log-content {
    max-height: 200px;
    overflow-y: auto;

    pre {
      margin: 0;
      white-space: pre-wrap;
      word-break: break-all;
      font-family: monospace;
      font-size: 12px;
      padding: 8px;
      border-radius: 4px;
    }
  }
}

:deep(.el-table__expanded-cell) {
  padding: 0 !important;
}
</style>
