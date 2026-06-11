import { createRouter, createWebHistory } from 'vue-router'
import Home from '@/pages/Home.vue'
import Dashboard from '@/pages/Dashboard.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'Home',
      component: Home
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: Dashboard
    },
  ],
  linkActiveClass: 'text-gray-300 hover:bg-white/5 hover:text-white',
  linkExactActiveClass: 'bg-gray-950/50'
})

export default router
