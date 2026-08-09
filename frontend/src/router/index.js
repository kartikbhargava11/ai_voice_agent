import { createRouter, createWebHistory } from 'vue-router'
import Home from '@/pages/Home.vue'
import Dashboard from '@/pages/Dashboard.vue'
import Login from '@/pages/Login.vue'

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
      component: Dashboard,
      meta: { requiresAuth: true }
    },
    {
      path: '/login',
      name: 'Login',
      component: Login,
      meta: { guestOnly: true }
    },
  ],
  linkActiveClass: 'text-gray-300 hover:bg-white/5 hover:text-white',
  linkExactActiveClass: 'bg-gray-950/50'
})

router.beforeEach((to) => {
  const isAuthenticated = Boolean(sessionStorage.getItem('auth_token'))

  if (to.meta.requiresAuth && !isAuthenticated) {
    return {
      name: 'Login',
      query: { redirect: to.fullPath }
    }
  }

  if (to.meta.guestOnly && isAuthenticated) {
    return { name: 'Dashboard' }
  }
})

export default router
