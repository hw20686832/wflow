<template>
  <div class="tasks-container">
    <h2>Tasks</h2>
    <el-table :data="tasks" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="Name" />
      <el-table-column prop="workflow_id" label="Workflow ID" width="120" />
      <el-table-column label="Command" width="300">
        <template #default="{ row }">
          <code>{{ Array.isArray(row.command) ? row.command.join(' ') : row.command }}</code>
        </template>
      </el-table-column>
      <el-table-column prop="retry_count" label="Retry" width="80" />
      <el-table-column prop="created_at" label="Created" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="Actions" width="150">
        <template #default="{ row }">
          <el-button size="small" @click="viewTask(row.workflow_id, row.id)">View</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../services/api'

export default {
  name: 'Tasks',
  setup() {
    const router = useRouter()
    const loading = ref(false)
    const tasks = ref([])
    
    const loadTasks = async () => {
      loading.value = true
      try {
        const workflowsResponse = await api.get('/workflows')
        const workflows = workflowsResponse.data.workflows
        
        let allTasks = []
        for (const workflow of workflows) {
          const tasksResponse = await api.get(`/workflows/${workflow.id}/tasks`)
          allTasks = [...allTasks, ...tasksResponse.data.tasks]
        }
        
        tasks.value = allTasks
      } catch (error) {
        ElMessage.error('Failed to load tasks')
      } finally {
        loading.value = false
      }
    }
    
    const viewTask = (workflowId, taskId) => {
      router.push(`/workflows/${workflowId}`)
    }
    
    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleString()
    }
    
    onMounted(() => {
      loadTasks()
    })
    
    return {
      loading,
      tasks,
      viewTask,
      formatDate
    }
  }
}
</script>

<style scoped>
.tasks-container {
  padding: 20px;
}

code {
  background-color: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
}
</style>
