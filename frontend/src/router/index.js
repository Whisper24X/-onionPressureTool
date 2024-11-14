import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/home/index.vue'

export const routes = [
  {
    path: '/',
    name: 'home',
    meta: {
      title: '首页',
    },
    component: HomeView,
  },
  {
    path: '/report',
    name: 'report',
    meta: {
      title: '报告',
    },
    component: () => import('../views/report/index.vue'),
  },
  {
    path: '/detail',
    name: 'detail',
    meta: {
      title: '详情',
      hiddenInMenu: true,
    },
    component: () => import('../views/detail/index.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

export default router
