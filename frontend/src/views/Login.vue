<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <h2>Login</h2>
        </div>
      </template>
      
      <el-form :model="loginForm" :rules="rules" ref="loginFormRef" label-width="80px">
        <el-form-item label="Username" prop="username">
          <el-input v-model="loginForm.username" placeholder="Enter your username" />
        </el-form-item>
        
        <el-form-item label="Password" prop="password">
          <el-input 
            v-model="loginForm.password" 
            type="password" 
            placeholder="Enter your password" 
            show-password
          />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleLogin" :loading="loading" style="width: 100%">
            Login
          </el-button>
        </el-form-item>
        
        <el-form-item>
          <div class="links">
            <router-link to="/register">Don't have an account? Register</router-link>
          </div>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

export default {
  name: 'Login',
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()
    const loginFormRef = ref(null)
    const loading = ref(false)
    
    const loginForm = reactive({
      username: '',
      password: ''
    })
    
    const rules = {
      username: [
        { required: true, message: 'Please enter username', trigger: 'blur' }
      ],
      password: [
        { required: true, message: 'Please enter password', trigger: 'blur' }
      ]
    }
    
    const handleLogin = async () => {
      if (!loginFormRef.value) return
      
      await loginFormRef.value.validate(async (valid) => {
        if (valid) {
          loading.value = true
          try {
            const success = await authStore.login(loginForm.username, loginForm.password)
            if (success) {
              ElMessage.success('Login successful')
              router.push('/workflows')
            } else {
              ElMessage.error('Invalid username or password')
            }
          } catch (error) {
            ElMessage.error('Login failed. Please try again.')
          } finally {
            loading.value = false
          }
        }
      })
    }
    
    return {
      loginForm,
      rules,
      loginFormRef,
      loading,
      handleLogin
    }
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 400px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.card-header {
  text-align: center;
}

.card-header h2 {
  margin: 0;
  color: #409EFF;
}

.links {
  width: 100%;
  text-align: center;
}

.links a {
  color: #409EFF;
  text-decoration: none;
}

.links a:hover {
  text-decoration: underline;
}
</style>
