import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/workflows',
    name: 'Workflows',
    component: () => import('../views/Workflows.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/workflows/:id',
    name: 'WorkflowDetail',
    component: () => import('../views/WorkflowDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/tasks',
    name: 'Tasks',
    component: () => import('../views/Tasks.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/executions',
    name: 'Executions',
    component: () => import('../views/Executions.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/',
    redirect: '/workflows'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if ((to.name === 'Login' || to.name === 'Register') && authStore.isAuthenticated) {
    next('/workflows')
  } else {
    next()
  }
})

export default router
