<template>
  <div class="workflow-detail-container">
    <div class="header">
      <el-button @click="$router.back()" :icon="ArrowLeft">Back</el-button>
      <h2>{{ workflow?.name }}</h2>
      <div class="actions">
        <el-button type="primary" @click="showTaskDialog = true">
          <el-icon><Plus /></el-icon>
          Add Task
        </el-button>
        <el-button type="success" @click="executeWorkflow">Execute</el-button>
        <el-button @click="exportWorkflow">Export</el-button>
      </div>
    </div>
    
    <el-card v-if="workflow" class="workflow-info">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="ID">{{ workflow.id }}</el-descriptions-item>
        <el-descriptions-item label="Name">{{ workflow.name }}</el-descriptions-item>
        <el-descriptions-item label="Description">{{ workflow.description || 'N/A' }}</el-descriptions-item>
        <el-descriptions-item label="Schedule">{{ workflow.schedule || 'N/A' }}</el-descriptions-item>
        <el-descriptions-item label="Executor">{{ workflow.executor }}</el-descriptions-item>
        <el-descriptions-item label="Type">{{ workflow.type }}</el-descriptions-item>
      </el-descriptions>
    </el-card>
    
    <el-card class="tasks-card">
      <template #header>
        <h3>Tasks</h3>
      </template>
      
      <el-table :data="tasks" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="Name" />
        <el-table-column label="Command" width="300">
          <template #default="{ row }">
            <code>{{ Array.isArray(row.command) ? row.command.join(' ') : row.command }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="retry_count" label="Retry" width="80" />
        <el-table-column label="Actions" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="viewTask(row.id)">View</el-button>
            <el-button size="small" type="danger" @click="deleteTask(row.id)">Delete</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <el-dialog v-model="showTaskDialog" title="Add Task" width="600px">
      <el-form :model="taskForm" :rules="taskRules" ref="taskFormRef" label-width="120px">
        <el-form-item label="Name" prop="name">
          <el-input v-model="taskForm.name" placeholder="Enter task name" />
        </el-form-item>
        
        <el-form-item label="Command" prop="command">
          <el-input 
            v-model="commandInput" 
            placeholder="Enter command (space separated)" 
            @blur="parseCommand"
          />
          <div class="command-hint">Example: python3 script.py arg1 arg2</div>
        </el-form-item>
        
        <el-form-item label="Retry Count" prop="retry_count">
          <el-input-number v-model="taskForm.retry_count" :min="0" :max="10" />
        </el-form-item>
        
        <el-form-item label="Retry Interval" prop="retry_interval">
          <el-input-number v-model="taskForm.retry_interval" :min="0" :max="3600" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showTaskDialog = false">Cancel</el-button>
        <el-button type="primary" @click="addTask" :loading="adding">Add</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Plus } from '@element-plus/icons-vue'
import api from '../services/api'

export default {
  name: 'WorkflowDetail',
  components: {
    ArrowLeft,
    Plus
  },
  setup() {
    const route = useRoute()
    const workflowId = route.params.id
    const loading = ref(false)
    const adding = ref(false)
    const workflow = ref(null)
    const tasks = ref([])
    const showTaskDialog = ref(false)
    const taskFormRef = ref(null)
    const commandInput = ref('')
    
    const taskForm = reactive({
      name: '',
      command: [],
      retry_count: 0,
      retry_interval: 0
    })
    
    const taskRules = {
      name: [
        { required: true, message: 'Please enter task name', trigger: 'blur' }
      ],
      command: [
        { required: true, message: 'Please enter command', trigger: 'blur' }
      ]
    }
    
    const loadWorkflow = async () => {
      loading.value = true
      try {
        const response = await api.get(`/workflows/${workflowId}`)
        workflow.value = response.data.workflow
        tasks.value = response.data.workflow.tasks || []
      } catch (error) {
        ElMessage.error('Failed to load workflow')
      } finally {
        loading.value = false
      }
    }
    
    const parseCommand = () => {
      if (commandInput.value.trim()) {
        taskForm.command = commandInput.value.trim().split(/\s+/)
      } else {
        taskForm.command = []
      }
    }
    
    const addTask = async () => {
      if (!taskFormRef.value) return
      
      parseCommand()
      
      await taskFormRef.value.validate(async (valid) => {
        if (valid) {
          adding.value = true
          try {
            await api.post(`/workflows/${workflowId}/tasks`, taskForm)
            ElMessage.success('Task added successfully')
            showTaskDialog.value = false
            resetTaskForm()
            loadWorkflow()
          } catch (error) {
            ElMessage.error('Failed to add task')
          } finally {
            adding.value = false
          }
        }
      })
    }
    
    const viewTask = (taskId) => {
      ElMessage.info('Task detail view coming soon')
    }
    
    const deleteTask = async (taskId) => {
      try {
        await ElMessageBox.confirm('Are you sure you want to delete this task?', 'Confirm', {
          type: 'warning'
        })
        
        await api.delete(`/workflows/${workflowId}/tasks/${taskId}`)
        ElMessage.success('Task deleted successfully')
        loadWorkflow()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('Failed to delete task')
        }
      }
    }
    
    const executeWorkflow = async () => {
      try {
        await ElMessageBox.confirm('Are you sure you want to execute this workflow?', 'Confirm', {
          type: 'warning'
        })
        
        await api.post(`/workflows/${workflowId}/execute`)
        ElMessage.success('Workflow execution started')
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('Failed to execute workflow')
        }
      }
    }
    
    const exportWorkflow = async () => {
      try {
        const response = await api.get(`/workflows/${workflowId}/export`, {
          responseType: 'blob'
        })
        
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `${workflow.value.name}.json`)
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        
        ElMessage.success('Workflow exported successfully')
      } catch (error) {
        ElMessage.error('Failed to export workflow')
      }
    }
    
    const resetTaskForm = () => {
      taskForm.name = ''
      taskForm.command = []
      taskForm.retry_count = 0
      taskForm.retry_interval = 0
      commandInput.value = ''
    }
    
    onMounted(() => {
      loadWorkflow()
    })
    
    return {
      workflowId,
      loading,
      adding,
      workflow,
      tasks,
      showTaskDialog,
      taskForm,
      taskRules,
      taskFormRef,
      commandInput,
      loadWorkflow,
      parseCommand,
      addTask,
      viewTask,
      deleteTask,
      executeWorkflow,
      exportWorkflow
    }
  }
}
</script>

<style scoped>
.workflow-detail-container {
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

.actions {
  display: flex;
  gap: 10px;
}

.workflow-info {
  margin-bottom: 20px;
}

.tasks-card {
  margin-bottom: 20px;
}

.tasks-card h3 {
  margin: 0;
}

.command-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

code {
  background-color: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
}
</style>
