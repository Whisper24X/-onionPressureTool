<script setup>
import { ElConfigProvider } from 'element-plus'

import zhCn from 'element-plus/es/locale/lang/zh-cn'

import AppLayout from '@/components/appLayout.vue'
</script>

<template>
  <ElConfigProvider :locale="zhCn">
    <AppLayout />
  </ElConfigProvider>
</template>

<style scoped lang="less"></style>
