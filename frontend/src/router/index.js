import { createRouter, createWebHashHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Tasks from '../views/Tasks.vue'
import Articles from '../views/Articles.vue'
import Sources from '../views/Sources.vue'

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/tasks',
    name: 'Tasks',
    component: Tasks
  },
  {
    path: '/articles',
    name: 'Articles',
    component: Articles
  },
  {
    path: '/sources',
    name: 'Sources',
    component: Sources
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router
