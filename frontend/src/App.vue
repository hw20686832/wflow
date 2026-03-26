<template>
  <div id="app">
    <el-container v-if="isAuthenticated">
      <el-header>
        <div class="header-content">
          <div class="logo">WFlow</div>
          <div class="user-info">
            <span>{{ currentUser.username }}</span>
            <el-button type="text" @click="logout">Logout</el-button>
          </div>
        </div>
      </el-header>
      <el-container>
        <el-aside width="200px">
          <el-menu
            :default-active="activeMenu"
            router
            background-color="#545c64"
            text-color="#fff"
            active-text-color="#ffd04b"
          >
            <el-menu-item index="/workflows">
              <el-icon><Document /></el-icon>
              <span>Workflows</span>
            </el-menu-item>
            <el-menu-item index="/tasks">
              <el-icon><List /></el-icon>
              <span>Tasks</span>
            </el-menu-item>
            <el-menu-item index="/executions">
              <el-icon><Clock /></el-icon>
              <span>Executions</span>
            </el-menu-item>
          </el-menu>
        </el-aside>
        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
    <div v-else class="auth-container">
      <router-view />
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Document, List, Clock } from '@element-plus/icons-vue'
import { useAuthStore } from './stores/auth'

export default {
  name: 'App',
  components: {
    Document,
    List,
    Clock
  },
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()
    
    const isAuthenticated = computed(() => authStore.isAuthenticated)
    const currentUser = computed(() => authStore.user)
    const activeMenu = computed(() => router.currentRoute.value.path)
    
    const logout = () => {
      authStore.logout()
      router.push('/login')
    }
    
    onMounted(() => {
      authStore.checkAuth()
    })
    
    return {
      isAuthenticated,
      currentUser,
      activeMenu,
      logout
    }
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  height: 100vh;
}

.el-header {
  background-color: #409EFF;
  color: white;
  line-height: 60px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
}

.logo {
  font-size: 24px;
  font-weight: bold;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.el-aside {
  background-color: #545c64;
  color: white;
}

.el-main {
  background-color: #f5f7fa;
  padding: 20px;
}

.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f5f7fa;
}
</style>
