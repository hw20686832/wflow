<template>
  <div class="workflows-container">
    <div class="header">
      <h2>Workflows</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        Create Workflow
      </el-button>
    </div>
    
    <el-table :data="workflows" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="Name" />
      <el-table-column prop="description" label="Description" />
      <el-table-column prop="schedule" label="Schedule" />
      <el-table-column prop="task_count" label="Tasks" width="80" />
      <el-table-column prop="created_at" label="Created" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="Actions" width="300">
        <template #default="{ row }">
          <el-button size="small" @click="viewWorkflow(row.id)">View</el-button>
          <el-button size="small" type="primary" @click="executeWorkflow(row.id)">Execute</el-button>
          <el-button size="small" type="danger" @click="deleteWorkflow(row.id)">Delete</el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <el-dialog v-model="showCreateDialog" title="Create Workflow" width="600px">
      <el-form :model="workflowForm" :rules="workflowRules" ref="workflowFormRef" label-width="120px">
        <el-form-item label="Name" prop="name">
          <el-input v-model="workflowForm.name" placeholder="Enter workflow name" />
        </el-form-item>
        
        <el-form-item label="Description" prop="description">
          <el-input 
            v-model="workflowForm.description" 
            type="textarea" 
            :rows="3"
            placeholder="Enter workflow description" 
          />
        </el-form-item>
        
        <el-form-item label="Schedule" prop="schedule">
          <el-input v-model="workflowForm.schedule" placeholder="e.g., 0 0 * * *" />
        </el-form-item>
        
        <el-form-item label="Executor" prop="executor">
          <el-select v-model="workflowForm.executor" placeholder="Select executor">
            <el-option label="Local" value="local" />
            <el-option label="Celery" value="celery" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="Type" prop="type">
          <el-select v-model="workflowForm.type" placeholder="Select type">
            <el-option label="Serial Flow" value="serialFlow" />
            <el-option label="Parallel Flow" value="parallelFlow" />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showCreateDialog = false">Cancel</el-button>
        <el-button type="primary" @click="createWorkflow" :loading="creating">Create</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import api from '../services/api'

export default {
  name: 'Workflows',
  components: {
    Plus
  },
  setup() {
    const router = useRouter()
    const loading = ref(false)
    const creating = ref(false)
    const workflows = ref([])
    const showCreateDialog = ref(false)
    const workflowFormRef = ref(null)
    
    const workflowForm = reactive({
      name: '',
      description: '',
      schedule: '',
      executor: 'local',
      type: 'serialFlow'
    })
    
    const workflowRules = {
      name: [
        { required: true, message: 'Please enter workflow name', trigger: 'blur' }
      ]
    }
    
    const loadWorkflows = async () => {
      loading.value = true
      try {
        const response = await api.get('/workflows')
        workflows.value = response.data.workflows
      } catch (error) {
        ElMessage.error('Failed to load workflows')
      } finally {
        loading.value = false
      }
    }
    
    const createWorkflow = async () => {
      if (!workflowFormRef.value) return
      
      await workflowFormRef.value.validate(async (valid) => {
        if (valid) {
          creating.value = true
          try {
            await api.post('/workflows', workflowForm)
            ElMessage.success('Workflow created successfully')
            showCreateDialog.value = false
            resetForm()
            loadWorkflows()
          } catch (error) {
            ElMessage.error('Failed to create workflow')
          } finally {
            creating.value = false
          }
        }
      })
    }
    
    const viewWorkflow = (id) => {
      router.push(`/workflows/${id}`)
    }
    
    const executeWorkflow = async (id) => {
      try {
        await ElMessageBox.confirm('Are you sure you want to execute this workflow?', 'Confirm', {
          type: 'warning'
        })
        
        await api.post(`/workflows/${id}/execute`)
        ElMessage.success('Workflow execution started')
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('Failed to execute workflow')
        }
      }
    }
    
    const deleteWorkflow = async (id) => {
      try {
        await ElMessageBox.confirm('Are you sure you want to delete this workflow?', 'Confirm', {
          type: 'warning'
        })
        
        await api.delete(`/workflows/${id}`)
        ElMessage.success('Workflow deleted successfully')
        loadWorkflows()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('Failed to delete workflow')
        }
      }
    }
    
    const resetForm = () => {
      workflowForm.name = ''
      workflowForm.description = ''
      workflowForm.schedule = ''
      workflowForm.executor = 'local'
      workflowForm.type = 'serialFlow'
    }
    
    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleString()
    }
    
    onMounted(() => {
      loadWorkflows()
    })
    
    return {
      loading,
      creating,
      workflows,
      showCreateDialog,
      workflowForm,
      workflowRules,
      workflowFormRef,
      loadWorkflows,
      createWorkflow,
      viewWorkflow,
      executeWorkflow,
      deleteWorkflow,
      formatDate
    }
  }
}
</script>

<style scoped>
.workflows-container {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h2 {
  margin: 0;
}
</style>
