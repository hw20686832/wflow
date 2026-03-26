<template>
  <div class="executions-container">
    <div class="header">
      <h2>Executions</h2>
      <el-select v-model="selectedWorkflow" placeholder="Select Workflow" @change="loadExecutions">
        <el-option label="All Workflows" :value="null" />
        <el-option 
          v-for="workflow in workflows" 
          :key="workflow.id" 
          :label="workflow.name" 
          :value="workflow.id"
        />
      </el-select>
    </div>
    
    <el-table :data="executions" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="workflow_id" label="Workflow" width="100" />
      <el-table-column prop="task_id" label="Task" width="100" />
      <el-table-column label="Status" width="120">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="start_time" label="Start Time" width="180">
        <template #default="{ row }">
          {{ formatDate(row.start_time) }}
        </template>
      </el-table-column>
      <el-table-column prop="end_time" label="End Time" width="180">
        <template #default="{ row }">
          {{ formatDate(row.end_time) }}
        </template>
      </el-table-column>
      <el-table-column prop="exit_code" label="Exit Code" width="100" />
      <el-table-column label="Actions" width="150">
        <template #default="{ row }">
          <el-button size="small" @click="viewExecution(row)">View</el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <el-dialog v-model="showLogDialog" title="Execution Log" width="800px">
      <div v-if="currentExecution" class="execution-info">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="ID">{{ currentExecution.id }}</el-descriptions-item>
          <el-descriptions-item label="Status">
            <el-tag :type="getStatusType(currentExecution.status)">{{ currentExecution.status }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="Start Time">{{ formatDate(currentExecution.start_time) }}</el-descriptions-item>
          <el-descriptions-item label="End Time">{{ formatDate(currentExecution.end_time) }}</el-descriptions-item>
          <el-descriptions-item label="Exit Code">{{ currentExecution.exit_code }}</el-descriptions-item>
          <el-descriptions-item label="Retry Count">{{ currentExecution.retry_count }}</el-descriptions-item>
        </el-descriptions>
      </div>
      
      <div v-if="currentExecution && currentExecution.error_message" class="error-message">
        <el-alert type="error" :closable="false">
          {{ currentExecution.error_message }}
        </el-alert>
      </div>
      
      <div class="log-content">
        <pre v-if="logs.length > 0">{{ logs.map(log => log.log_content).join('\n') }}</pre>
        <div v-else class="no-logs">No logs available</div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../services/api'

export default {
  name: 'Executions',
  setup() {
    const loading = ref(false)
    const executions = ref([])
    const workflows = ref([])
    const selectedWorkflow = ref(null)
    const showLogDialog = ref(false)
    const currentExecution = ref(null)
    const logs = ref([])
    
    const loadWorkflows = async () => {
      try {
        const response = await api.get('/workflows')
        workflows.value = response.data.workflows
      } catch (error) {
        ElMessage.error('Failed to load workflows')
      }
    }
    
    const loadExecutions = async () => {
      loading.value = true
      try {
        let response
        if (selectedWorkflow.value) {
          response = await api.get(`/workflows/${selectedWorkflow.value}/executions`)
        } else {
          const workflowsResponse = await api.get('/workflows')
          const workflowList = workflowsResponse.data.workflows
          
          let allExecutions = []
          for (const workflow of workflowList) {
            const execResponse = await api.get(`/workflows/${workflow.id}/executions`)
            allExecutions = [...allExecutions, ...execResponse.data.executions]
          }
          
          executions.value = allExecutions.sort((a, b) => 
            new Date(b.created_at) - new Date(a.created_at)
          )
          return
        }
        
        executions.value = response.data.executions
      } catch (error) {
        ElMessage.error('Failed to load executions')
      } finally {
        loading.value = false
      }
    }
    
    const viewExecution = async (execution) => {
      currentExecution.value = execution
      logs.value = []
      
      try {
        const response = await api.get(
          `/workflows/${execution.workflow_id}/executions/${execution.id}`
        )
        
        if (response.data.execution && response.data.execution.logs) {
          logs.value = response.data.execution.logs
        }
        
        showLogDialog.value = true
      } catch (error) {
        ElMessage.error('Failed to load execution details')
      }
    }
    
    const getStatusType = (status) => {
      const statusMap = {
        'pending': 'info',
        'running': 'warning',
        'success': 'success',
        'failed': 'danger',
        'skipped': 'info'
      }
      return statusMap[status] || 'info'
    }
    
    const formatDate = (dateString) => {
      if (!dateString) return 'N/A'
      return new Date(dateString).toLocaleString()
    }
    
    onMounted(() => {
      loadWorkflows()
      loadExecutions()
    })
    
    return {
      loading,
      executions,
      workflows,
      selectedWorkflow,
      showLogDialog,
      currentExecution,
      logs,
      loadExecutions,
      viewExecution,
      getStatusType,
      formatDate
    }
  }
}
</script>

<style scoped>
.executions-container {
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

.execution-info {
  margin-bottom: 20px;
}

.error-message {
  margin-bottom: 20px;
}

.log-content {
  background-color: #1e1e1e;
  color: #d4d4d4;
  padding: 15px;
  border-radius: 4px;
  max-height: 400px;
  overflow-y: auto;
}

.log-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

.no-logs {
  color: #909399;
  text-align: center;
  padding: 20px;
}
</style>
