<template>
  <div class="register-container">
    <el-card class="register-card">
      <template #header>
        <div class="card-header">
          <h2>Register</h2>
        </div>
      </template>
      
      <el-form :model="registerForm" :rules="rules" ref="registerFormRef" label-width="80px">
        <el-form-item label="Username" prop="username">
          <el-input v-model="registerForm.username" placeholder="Enter your username" />
        </el-form-item>
        
        <el-form-item label="Email" prop="email">
          <el-input v-model="registerForm.email" placeholder="Enter your email" />
        </el-form-item>
        
        <el-form-item label="Password" prop="password">
          <el-input 
            v-model="registerForm.password" 
            type="password" 
            placeholder="Enter your password" 
            show-password
          />
        </el-form-item>
        
        <el-form-item label="Confirm" prop="confirmPassword">
          <el-input 
            v-model="registerForm.confirmPassword" 
            type="password" 
            placeholder="Confirm your password" 
            show-password
          />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleRegister" :loading="loading" style="width: 100%">
            Register
          </el-button>
        </el-form-item>
        
        <el-form-item>
          <div class="links">
            <router-link to="/login">Already have an account? Login</router-link>
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
  name: 'Register',
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()
    const registerFormRef = ref(null)
    const loading = ref(false)
    
    const registerForm = reactive({
      username: '',
      email: '',
      password: '',
      confirmPassword: ''
    })
    
    const validateConfirmPassword = (rule, value, callback) => {
      if (value !== registerForm.password) {
        callback(new Error('Passwords do not match'))
      } else {
        callback()
      }
    }
    
    const rules = {
      username: [
        { required: true, message: 'Please enter username', trigger: 'blur' },
        { min: 3, max: 50, message: 'Username must be 3-50 characters', trigger: 'blur' }
      ],
      email: [
        { required: true, message: 'Please enter email', trigger: 'blur' },
        { type: 'email', message: 'Please enter valid email', trigger: 'blur' }
      ],
      password: [
        { required: true, message: 'Please enter password', trigger: 'blur' },
        { min: 6, message: 'Password must be at least 6 characters', trigger: 'blur' }
      ],
      confirmPassword: [
        { required: true, message: 'Please confirm password', trigger: 'blur' },
        { validator: validateConfirmPassword, trigger: 'blur' }
      ]
    }
    
    const handleRegister = async () => {
      if (!registerFormRef.value) return
      
      await registerFormRef.value.validate(async (valid) => {
        if (valid) {
          loading.value = true
          try {
            const success = await authStore.register(
              registerForm.username,
              registerForm.password,
              registerForm.email
            )
            if (success) {
              ElMessage.success('Registration successful. Please login.')
              router.push('/login')
            } else {
              ElMessage.error('Registration failed. Username or email may already exist.')
            }
          } catch (error) {
            ElMessage.error('Registration failed. Please try again.')
          } finally {
            loading.value = false
          }
        }
      })
    }
    
    return {
      registerForm,
      rules,
      registerFormRef,
      loading,
      handleRegister
    }
  }
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.register-card {
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
