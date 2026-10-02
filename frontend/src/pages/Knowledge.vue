<template>
  <div class="page-container knowledge-page">
    <PageHeader :title="PAGE_HEADERS.knowledge.title" :subtitle="PAGE_HEADERS.knowledge.subtitle" />

    <el-row :gutter="24">
      <el-col :span="8">
        <div class="card-panel uploader-panel" v-loading="uploading || rebuilding">
          <h3 class="section-heading">上传课程资料</h3>

          <div
            class="upload-drop"
            @click="openFilePicker"
            @dragover.prevent
            @drop.prevent="onDropFiles"
          >
            <el-icon :size="34"><UploadFilled /></el-icon>
            <strong>选择或拖入文件</strong>
            <p>支持 PDF、PPTX、DOCX、TXT，上传后会自动重建知识库</p>
          </div>

          <input
            ref="fileInputRef"
            class="file-input"
            type="file"
            multiple
            accept=".pdf,.pptx,.docx,.txt"
            @change="onFileInputChange"
          />

          <div v-if="selectedFiles.length" class="selected-files">
            <div v-for="file in selectedFiles" :key="file.name" class="selected-file">
              <span>{{ file.name }}</span>
              <small>{{ formatSize(file.size) }}</small>
            </div>
          </div>

          <div class="action-row">
            <el-button type="primary" class="gradient-btn" :loading="uploading" :disabled="!selectedFiles.length" @click="uploadFiles">
              上传并重建
            </el-button>
            <el-button plain @click="clearSelectedFiles">清空选择</el-button>
          </div>

          <div class="rebuild-box">
            <h4>已有文件重建</h4>
            <p>当你直接把文件放入后端 docs 文件夹后，可在这里手动重建向量库。</p>
            <el-button type="warning" plain :loading="rebuilding" @click="rebuild">
              重新构建知识库
            </el-button>
          </div>
        </div>
      </el-col>

      <el-col :span="16">
        <div class="status-grid">
          <div class="status-card glass-panel">
            <span class="status-num">{{ files.length }}</span>
            <span class="status-label">知识库文件</span>
          </div>
          <div class="status-card glass-panel">
            <span class="status-num">{{ vectorStatus.chunk_count || 0 }}</span>
            <span class="status-label">知识片段</span>
          </div>
          <div class="status-card glass-panel">
            <span class="status-num">{{ vectorStatus.exists ? '已构建' : '未构建' }}</span>
            <span class="status-label">向量库状态</span>
          </div>
        </div>

        <div class="card-panel file-panel">
          <div class="panel-header">
            <h3 class="section-heading">当前知识库文件</h3>
            <el-button size="small" :loading="loading" @click="loadStatus">刷新</el-button>
          </div>

          <el-table v-if="files.length" :data="files" stripe>
            <el-table-column prop="name" label="文件名" min-width="220" />
            <el-table-column prop="suffix" label="类型" width="90">
              <template #default="{ row }">
                <el-tag size="small" effect="light">{{ row.suffix }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="大小" width="110">
              <template #default="{ row }">{{ formatSize(row.size) }}</template>
            </el-table-column>
            <el-table-column label="更新时间" width="180">
              <template #default="{ row }">{{ formatTime(row.updated_at) }}</template>
            </el-table-column>
          </el-table>

          <EmptyState
            v-else
            title="暂无知识库文件"
            hint="上传课程资料后，AI 问答与资源生成会优先检索这些资料"
            :icon="FolderOpened"
          />
        </div>

        <div v-if="lastResult" class="card-panel result-panel">
          <h3 class="section-heading">最近构建结果</h3>
          <div class="result-list">
            <div>
              <span>保存文件</span>
              <strong>{{ lastResult.saved_files?.length || 0 }}</strong>
            </div>
            <div>
              <span>读取文档</span>
              <strong>{{ lastResult.rebuild?.document_count || lastResult.document_count || 0 }}</strong>
            </div>
            <div>
              <span>知识片段</span>
              <strong>{{ lastResult.rebuild?.chunk_count || lastResult.chunk_count || 0 }}</strong>
            </div>
          </div>
          <div v-if="lastResult.skipped_files?.length" class="skip-list">
            <el-tag v-for="item in lastResult.skipped_files" :key="item.name" type="warning" effect="light">
              {{ item.name }}：{{ item.reason }}
            </el-tag>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { FolderOpened, UploadFilled } from '@element-plus/icons-vue'
import { getKnowledgeBaseStatus, rebuildKnowledgeBase, uploadKnowledgeBaseFiles } from '@/api/index'
import PageHeader from '@/components/PageHeader.vue'
import EmptyState from '@/components/EmptyState.vue'
import { PAGE_HEADERS } from '@/constants/brand'

const SUPPORTED_SUFFIXES = ['.pdf', '.pptx', '.docx', '.txt']

const fileInputRef = ref(null)
const loading = ref(false)
const uploading = ref(false)
const rebuilding = ref(false)
const status = ref({})
const selectedFiles = ref([])
const lastResult = ref(null)

const files = computed(() => status.value.files || [])
const vectorStatus = computed(() => status.value.vector_db || {})

function openFilePicker() {
  fileInputRef.value?.click()
}

function normalizeFileList(fileList) {
  return Array.from(fileList || []).filter((file) => {
    const suffix = getSuffix(file.name)
    return SUPPORTED_SUFFIXES.includes(suffix)
  })
}

function getSuffix(name) {
  const index = name.lastIndexOf('.')
  return index >= 0 ? name.slice(index).toLowerCase() : ''
}

function setSelectedFiles(fileList) {
  const next = normalizeFileList(fileList)
  if (!next.length) {
    ElMessage.warning('请选择 pdf、pptx、docx 或 txt 文件')
    return
  }
  selectedFiles.value = next
}

function onFileInputChange(event) {
  setSelectedFiles(event.target.files)
  event.target.value = ''
}

function onDropFiles(event) {
  setSelectedFiles(event.dataTransfer?.files)
}

function clearSelectedFiles() {
  selectedFiles.value = []
}

async function loadStatus() {
  loading.value = true
  try {
    status.value = await getKnowledgeBaseStatus()
  } finally {
    loading.value = false
  }
}

async function uploadFiles() {
  if (!selectedFiles.value.length) return
  uploading.value = true
  try {
    const result = await uploadKnowledgeBaseFiles(selectedFiles.value)
    lastResult.value = result
    status.value = {
      ...status.value,
      files: result.files || [],
      vector_db: result.rebuild?.vector_db || status.value.vector_db
    }
    selectedFiles.value = []
    ElMessage.success('知识库文件已上传，向量库已重建')
  } finally {
    uploading.value = false
  }
}

async function rebuild() {
  rebuilding.value = true
  try {
    const result = await rebuildKnowledgeBase()
    lastResult.value = result.rebuild || result
    status.value = {
      ...status.value,
      files: result.files || status.value.files || [],
      vector_db: result.rebuild?.vector_db || status.value.vector_db
    }
    ElMessage.success('知识库重建完成')
  } finally {
    rebuilding.value = false
  }
}

function formatSize(size = 0) {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

function formatTime(timestamp) {
  if (!timestamp) return '-'
  return new Date(timestamp * 1000).toLocaleString()
}

onMounted(loadStatus)
</script>

<style scoped>
.uploader-panel,
.file-panel,
.result-panel {
  margin-bottom: 20px;
}

.upload-drop {
  border: 1px dashed rgba(99, 102, 241, 0.36);
  border-radius: 16px;
  padding: 34px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  text-align: center;
  cursor: pointer;
  background: var(--bg-light);
  color: var(--primary-dark);
  transition: border-color 0.2s, background-color 0.2s;
}

.upload-drop:hover {
  border-color: var(--primary);
  background: rgba(99, 102, 241, 0.06);
}

.upload-drop strong {
  font-size: 16px;
}

.upload-drop p,
.rebuild-box p {
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-secondary);
}

.file-input {
  display: none;
}

.selected-files {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 16px;
}

.selected-file {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: #fff;
  font-size: 13px;
}

.selected-file span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.selected-file small {
  color: var(--text-secondary);
  flex-shrink: 0;
}

.action-row {
  display: flex;
  gap: 10px;
  margin-top: 18px;
  flex-wrap: wrap;
}

.rebuild-box {
  margin-top: 22px;
  padding-top: 18px;
  border-top: 1px solid var(--border);
}

.rebuild-box h4 {
  font-size: 14px;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.rebuild-box .el-button {
  margin-top: 12px;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  margin-bottom: 20px;
}

.status-card {
  padding: 18px;
  text-align: center;
}

.status-num {
  display: block;
  font-size: 24px;
  font-weight: 800;
  color: var(--primary-dark);
}

.status-label {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-secondary);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.panel-header .section-heading {
  margin-bottom: 0;
}

.result-list {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.result-list div {
  padding: 14px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--bg-light);
}

.result-list span {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
}

.result-list strong {
  display: block;
  margin-top: 4px;
  font-size: 22px;
  color: var(--primary-dark);
}

.skip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}
</style>
