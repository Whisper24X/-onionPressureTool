<template>
  <el-container class="common-layout">
    <el-aside width="200px" class="sider">
      <div class="logo">
        <h3>Perf性能平台</h3>
      </div>

      <ElMenu
        class="menu-wrap"
        active-text-color="#ffd04b"
        text-color="#fff"
        background-color="#545c64"
        :default-active="route.path"
        @select="selectMenu"
        router
      >
        <ElMenuItem v-for="({ path, name, meta }, idx) in menus" :key="name + idx" :index="path">
          {{ meta.title || '菜单标题' }}
        </ElMenuItem>
      </ElMenu>
    </el-aside>
    <el-main class="main"> <RouterView /> </el-main>
  </el-container>
</template>

<script setup>
import { RouterView, useRoute } from 'vue-router'

import { ElContainer, ElAside, ElMain, ElMenu, ElMenuItem } from 'element-plus'

defineOptions({ name: 'AppLayout' })

import { routes } from '@/router'

const route = useRoute()

const menus = routes.filter((v) => !v.meta?.hiddenInMenu)

const selectMenu = (key) => {
  console.log('selectMenu', key)
}
</script>

<style lang="less" scoped>
.common-layout {
  overflow: hidden;
  height: 100%;
  display: flex;
  background: var(--el-color-white);

  .sider {
    flex-shrink: 0;
    background-color: #545c64;

    .logo {
      h3 {
        color: #fff;
        font-size: 26px;
        text-align: center;
        padding: 8px 0;
      }
    }
    .menu-wrap {
      background-color: #545c64;
      border-right: 0;

      .el-menu-item.is-active {
        background-color: var(--el-menu-hover-bg-color);
      }
    }
  }

  .main {
    flex-grow: 1;
    overflow-y: auto;
  }
}
</style>
