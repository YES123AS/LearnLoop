<template>
  <div class="login-page">
    <div class="login-glow glow-one"></div>
    <div class="login-glow glow-two"></div>

    <div class="login-shell">
      <section class="hero-panel card-panel">
        <div class="hero-badge">AI 个性化学习 · 家校师协同</div>
        <LogoIcon :size="72" />
        <h1>智能学习协同管理平台</h1>
        <p class="hero-subtitle">面向学生、教师、家长的 AI 个性化学习与家校协同平台</p>

        <div class="feature-grid">
          <div class="feature-item">
            <strong>学生</strong>
            <span>AI 学习、练习、错题、路径规划</span>
          </div>
          <div class="feature-item">
            <strong>教师</strong>
            <span>学情管控、任务督导、批改反馈</span>
          </div>
          <div class="feature-item">
            <strong>家长</strong>
            <span>学习报告、教师反馈、家庭辅导建议</span>
          </div>
        </div>
      </section>

      <section class="login-panel card-panel">
        <div class="panel-head">
          <h2>欢迎登录</h2>
          <p>请选择身份后使用对应账号进入系统</p>
        </div>

        <div class="role-card-group">
          <button v-for="item in roleCards" :key="item.role" class="role-card" :class="{ active: form.role === item.role }" type="button" @click="selectRole(item.role)">
            <span class="role-title">{{ item.label }}</span>
            <span class="role-desc">{{ item.desc }}</span>
          </button>
        </div>

        <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent>
          <el-form-item label="账号" prop="username">
            <el-input v-model="form.username" placeholder="请输入账号" autocomplete="username" />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" autocomplete="current-password" />
          </el-form-item>

          <el-alert v-if="errorMsg" :title="errorMsg" type="error" show-icon :closable="false" class="mb12" />
          <el-button type="primary" class="gradient-btn submit-btn" :loading="loading" @click="handleLogin">{{ loading ? '登录中...' : '登录' }}</el-button>
        </el-form>

        <div class="tips">
          <span>演示账号</span>
          <div class="tip-list">
            <code>student / 123456</code>
            <code>teacher / 123456</code>
            <code>parent / 123456</code>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'
import { BRAND_NAME } from '@/constants/brand'
import LogoIcon from '@/components/LogoIcon.vue'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref()
const loading = ref(false)
const errorMsg = ref('')
const roleCards = [
  { role: 'student', label: '学生', desc: 'AI 学习、练习、错题、路径规划' },
  { role: 'teacher', label: '教师', desc: '学情管控、任务督导、批改反馈' },
  { role: 'parent', label: '家长', desc: '学习报告、教师反馈、家庭辅导建议' }
]
const form = reactive({ role: 'student', username: 'student', password: '123456' })
const rules = { role: [{ required: true, message: '请选择身份', trigger: 'change' }], username: [{ required: true, message: '请输入账号', trigger: 'blur' }], password: [{ required: true, message: '请输入密码', trigger: 'blur' }] }
const homeMap = { student: '/dashboard', teacher: '/teacher/dashboard', parent: '/parent/dashboard' }
function selectRole(role){ form.role = role; form.username = role; form.password = '123456'; errorMsg.value = '' }
async function handleLogin(){ errorMsg.value=''; await formRef.value?.validate(async (valid)=>{ if(!valid) return; loading.value=true; try{ userStore.login(form); ElMessage.success('登录成功'); await router.replace(homeMap[userStore.role]) }catch(err){ errorMsg.value=err?.message || '登录失败，请检查账号、密码或身份是否正确' }finally{ loading.value=false } }) }
onMounted(()=>{ if(userStore.isLoggedIn) router.replace(userStore.getHomeByRole()) })
</script>

<style scoped>
.login-page{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px;background:radial-gradient(circle at top left,#eef2ff 0,#f8fafc 45%,#eef2ff 100%);position:relative;overflow:hidden}.login-shell{width:min(1180px,100%);display:grid;grid-template-columns:1.1fr .9fr;gap:24px;z-index:1}.hero-panel{padding:36px 34px;background:linear-gradient(135deg,#fff 0,#f8f7ff 100%)}.hero-badge{display:inline-flex;padding:6px 12px;border-radius:999px;background:rgba(99,102,241,.12);color:var(--primary);font-size:12px;font-weight:600;margin-bottom:18px}.hero-panel h1{font-size:36px;margin:14px 0 8px}.hero-subtitle{color:var(--text-secondary);line-height:1.9;max-width:540px}.feature-grid{display:grid;grid-template-columns:1fr;gap:12px;margin-top:28px}.feature-item{padding:16px 18px;border:1px solid var(--border);border-radius:16px;background:rgba(255,255,255,.76)}.feature-item strong{display:block;font-size:15px;margin-bottom:4px}.feature-item span{color:var(--text-secondary);font-size:13px;line-height:1.6}.login-panel{padding:34px}.panel-head h2{font-size:26px;margin-bottom:6px}.panel-head p{color:var(--text-secondary);margin-bottom:20px}.role-card-group{display:grid;grid-template-columns:1fr;gap:10px;margin-bottom:18px}.role-card{border:1px solid var(--border);background:var(--bg-light);border-radius:16px;padding:14px 16px;text-align:left;cursor:pointer;transition:.2s}.role-card.active{border-color:var(--primary);background:rgba(99,102,241,.08);box-shadow:0 6px 18px rgba(99,102,241,.08)}.role-title{display:block;font-weight:700;margin-bottom:4px}.role-desc{display:block;color:var(--text-secondary);font-size:13px;line-height:1.6}.submit-btn{width:100%;height:44px;margin-top:8px}.tips{margin-top:18px}.tips>span{display:block;color:var(--text-secondary);font-size:12px;margin-bottom:8px}.tip-list{display:flex;gap:8px;flex-wrap:wrap}.tip-list code{background:rgba(99,102,241,.08);padding:4px 8px;border-radius:8px}.mb12{margin-bottom:12px}.login-glow{position:absolute;border-radius:50%;filter:blur(40px);opacity:.45}.glow-one{width:220px;height:220px;left:-40px;top:-40px;background:#c4b5fd}.glow-two{width:260px;height:260px;right:-80px;bottom:-80px;background:#93c5fd}.login-page :deep(.el-form-item__label){font-weight:600}@media(max-width:960px){.login-shell{grid-template-columns:1fr}.hero-panel{display:none}}</style>
