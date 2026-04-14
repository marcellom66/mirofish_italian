<template>
  <div class="home-container">
    <nav class="navbar">
      <div class="nav-brand">{{ $t('nav.brand') }}</div>
      <div class="nav-links">
        <a href="https://github.com/666ghj/MiroFish" target="_blank" class="github-link">
          {{ $t('nav.github') }} <span class="arrow">↗</span>
        </a>
      </div>
    </nav>

    <div class="main-content">
      <section class="hero-section">
        <div class="hero-left">
          <div class="tag-row">
            <span class="orange-tag">{{ $t('home.hero.title') }}</span>
            <span class="version-text">{{ $t('home.hero.version') }}</span>
          </div>

          <h1 class="main-title">
            {{ $t('home.hero.upload') }}<br>
            <span class="gradient-text">{{ $t('home.hero.simulate') }}</span>
          </h1>

          <div class="hero-desc">
            <p>
              {{ $t('home.hero.description') }}
            </p>
            <p class="slogan-text">
              {{ $t('home.hero.tagline') }}<span class="blinking-cursor">_</span>
            </p>
          </div>
           
          <div class="decoration-square"></div>
        </div>
        
        <div class="hero-right">
          <!-- Logo area -->
          <div class="logo-container">
            <img src="../assets/logo/MiroFish_logo_left.jpeg" alt="MiroFish Logo" class="hero-logo" />
          </div>
          
          <button class="scroll-down-btn" @click="scrollToBottom">
            ↓
          </button>
        </div>
      </section>

      <!-- {{ $t('home.quickTest.button') }} Templates -->
      <section class="quick-test-section">
        <div class="quick-test-header">
          <span class="status-dot">■</span>
          <span class="quick-test-label">{{ $t('home.quickTest.button') }}</span>
          <span class="quick-test-subtitle">{{ $t('home.quickTest.subtitle') }}</span>
        </div>
        <div class="template-cards">
          <div
            v-for="tmpl in templates"
            :key="tmpl.id"
            class="template-card"
            @click="openTemplate(tmpl)"
          >
            <span class="card-icon">{{ tmpl.icon }}</span>
            <div class="card-text">
              <div class="card-title">{{ getTemplateTitle(tmpl) }}</div>
              <div class="card-subtitle">{{ getTemplateSubtitle(tmpl) }}</div>
            </div>
            <span class="card-arrow">→</span>
          </div>
        </div>
      </section>

      <!-- Business Plan Analysis Section -->
      <section class="quick-test-section business-plan-section">
        <div class="quick-test-header">
          <span class="status-dot bp-dot">■</span>
          <span class="quick-test-label">{{ $t('businessPlan.sectionTitle') }}</span>
          <span class="quick-test-subtitle">{{ $t('businessPlan.sectionSubtitle') }}</span>
        </div>
        <div class="template-cards">
          <div
            v-for="tmpl in bpTemplates"
            :key="tmpl.id"
            class="template-card business-plan-card"
            @click="selectedBPTemplate = tmpl; showBPModal = true"
          >
            <span class="card-icon">{{ tmpl.icon }}</span>
            <div class="card-text">
              <div class="card-title">{{ t(tmpl.titleKey) }}</div>
              <div class="card-subtitle">{{ t(tmpl.subtitleKey) }}</div>
            </div>
            <span class="card-arrow">→</span>
          </div>
        </div>
      </section>

      <section class="dashboard-section">
        <div class="left-panel">
          <div class="panel-header">
            <span class="status-dot">■</span> {{ $t('home.features.systemStatus') }}
          </div>

          <h2 class="section-title">{{ $t('home.features.ready') }}</h2>
          <p class="section-desc">
            {{ $t('home.features.predictionEngine') }}
          </p>

          <div class="metrics-row">
            <div class="metric-card">
              <div class="metric-value">{{ $t('home.features.lowCost') }}</div>
              <div class="metric-label">{{ $t('home.features.avgCost') }}</div>
            </div>
            <div class="metric-card">
              <div class="metric-value">{{ $t('home.features.scalable') }}</div>
              <div class="metric-label">{{ $t('home.features.maxAgents') }}</div>
            </div>
          </div>

          <div class="steps-container">
            <div class="steps-header">
               <span class="diamond-icon">◇</span> {{ $t('home.workflow.title') }}
            </div>
            <div class="workflow-list">
              <div class="workflow-item">
                <span class="step-num">01</span>
                <div class="step-info">
                  <div class="step-title">{{ $t('home.workflow.graphBuild') }}</div>
                  <div class="step-desc">{{ $t('home.workflow.graphBuildDesc') }}</div>
                </div>
              </div>
              <div class="workflow-item">
                <span class="step-num">02</span>
                <div class="step-info">
                  <div class="step-title">{{ $t('home.workflow.envSetup') }}</div>
                  <div class="step-desc">{{ $t('home.workflow.envSetupDesc') }}</div>
                </div>
              </div>
              <div class="workflow-item">
                <span class="step-num">03</span>
                <div class="step-info">
                  <div class="step-title">{{ $t('home.workflow.simulation') }}</div>
                  <div class="step-desc">{{ $t('home.workflow.simulationDesc') }}</div>
                </div>
              </div>
              <div class="workflow-item">
                <span class="step-num">04</span>
                <div class="step-info">
                  <div class="step-title">{{ $t('home.workflow.report') }}</div>
                  <div class="step-desc">{{ $t('home.workflow.reportDesc') }}</div>
                </div>
              </div>
              <div class="workflow-item">
                <span class="step-num">05</span>
                <div class="step-info">
                  <div class="step-title">{{ $t('home.workflow.interaction') }}</div>
                  <div class="step-desc">{{ $t('home.workflow.interactionDesc') }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="right-panel">
          <div class="console-box">
            <div class="console-section">
              <div class="console-header">
                <span class="console-label">{{ $t('home.upload.title') }}</span>
                <span class="console-meta">{{ $t('home.upload.formats') }}</span>
              </div>
              
              <div 
                class="upload-zone"
                :class="{ 'drag-over': isDragOver, 'has-files': files.length > 0 }"
                @dragover.prevent="handleDragOver"
                @dragleave.prevent="handleDragLeave"
                @drop.prevent="handleDrop"
                @click="triggerFileInput"
              >
                <input
                  ref="fileInput"
                  type="file"
                  multiple
                  accept=".pdf,.md,.txt"
                  @change="handleFileSelect"
                  style="display: none"
                  :disabled="loading"
                />
                
                <div v-if="files.length === 0" class="upload-placeholder">
                  <div class="upload-icon">↑</div>
                  <div class="upload-title">{{ $t('home.upload.dragDrop') }}</div>
                  <div class="upload-hint">{{ $t('home.upload.orBrowse') }}</div>
                </div>
                
                <div v-else class="file-list">
                  <div v-for="(file, index) in files" :key="index" class="file-item">
                    <span class="file-icon">📄</span>
                    <span class="file-name">{{ file.name }}</span>
                    <button @click.stop="removeFile(index)" class="remove-btn">×</button>
                  </div>
                </div>
              </div>
            </div>

            <div class="console-divider">
              <span>{{ $t('home.upload.params') }}</span>
            </div>

            <div class="console-section">
              <div class="console-header">
                <span class="console-label">>_ {{ $t('home.upload.simulationPrompt') }}</span>
              </div>
              <div class="input-wrapper">
                <textarea
                  v-model="formData.simulationRequirement"
                  class="code-input"
                  :placeholder="$t('home.upload.placeholder')"
                  rows="6"
                  :disabled="loading"
                ></textarea>
                <div class="model-badge">{{ $t('home.upload.engine') }}</div>
              </div>
            </div>

            <div class="console-section btn-section">
              <button
                class="start-engine-btn"
                @click="startSimulation"
                :disabled="!canSubmit || loading"
              >
                <span v-if="!loading">{{ $t('home.upload.launch') }}</span>
                <span v-else>{{ $t('home.upload.initializing') }}</span>
                <span class="btn-arrow">→</span>
              </button>
            </div>
          </div>
        </div>
      </section>

      <HistoryDatabase />
    </div>

    <!-- {{ $t('home.quickTest.button') }} Modal -->
    <QuickTestModal
      v-if="selectedTemplate"
      :template="selectedTemplate"
      @close="selectedTemplate = null"
    />

    <!-- Business Plan Modal -->
    <BusinessPlanModal
      v-if="showBPModal && selectedBPTemplate"
      :template="selectedBPTemplate"
      :is-open="showBPModal"
      @close="showBPModal = false"
    />
  </div>
</template>

<script setup>
/**
 * Home.vue — Landing page and main entry point
 *
 * Contains:
 *   - Hero section with branding and navigation
 *   - Quick-test template cards for one-click simulation setup
 *   - System status dashboard with workflow steps overview
 *   - File upload zone (drag-and-drop) with simulation requirement input
 *   - HistoryDatabase component for past simulations
 *   - QuickTestModal for template-based quick testing
 *
 * On submit, files and requirements are stored via pendingUpload store
 * and the user is navigated to the Process page.
 */
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import HistoryDatabase from '../components/HistoryDatabase.vue'
import QuickTestModal from '../components/QuickTestModal.vue'
import BusinessPlanModal from '../components/BusinessPlanModal.vue'
import { QUICK_TEST_TEMPLATES } from '../config/quickTestTemplates'

const { t } = useI18n()
const templates = QUICK_TEST_TEMPLATES.filter(tmpl => tmpl.type !== 'business_plan')
const bpTemplates = QUICK_TEST_TEMPLATES.filter(tmpl => tmpl.type === 'business_plan')
const selectedTemplate = ref(null)

/** State for Business Plan modal */
const selectedBPTemplate = ref(null)
const showBPModal = ref(false)

/** Get the localized title for a quick-test template */
const getTemplateTitle = (tmpl) => t(tmpl.titleKey)
/** Get the localized subtitle for a quick-test template */
const getTemplateSubtitle = (tmpl) => t(tmpl.subtitleKey)

/** Open the QuickTestModal for a specific template */
const openTemplate = (tmpl) => {
  selectedTemplate.value = tmpl
}

const router = useRouter()

// ─── Form State ───────────────────────────────────────────────────────────────

/** @type {import('vue').Ref<{simulationRequirement: string}>} Form data */
const formData = ref({
  simulationRequirement: ''
})

/** @type {import('vue').Ref<File[]>} Uploaded document files */
const files = ref([])

/** @type {import('vue').Ref<boolean>} Whether a submission is in progress */
const loading = ref(false)

/** @type {import('vue').Ref<string>} Error message */
const error = ref('')

/** @type {import('vue').Ref<boolean>} Whether files are being dragged over the upload zone */
const isDragOver = ref(false)

/** @type {import('vue').Ref<HTMLInputElement|null>} Reference to the hidden file input element */
const fileInput = ref(null)

// ─── Computed Properties ──────────────────────────────────────────────────────

/** Whether the form is valid and can be submitted (requires files + requirement text) */
const canSubmit = computed(() => {
  return formData.value.simulationRequirement.trim() !== '' && files.value.length > 0
})

// ─── File Handling ────────────────────────────────────────────────────────────

/** Open the native file picker dialog */
const triggerFileInput = () => {
  if (!loading.value) {
    fileInput.value?.click()
  }
}

/** Handle files selected via the native file picker */
const handleFileSelect = (event) => {
  const selectedFiles = Array.from(event.target.files)
  addFiles(selectedFiles)
}

/** Set drag-over visual state */
const handleDragOver = (e) => {
  if (!loading.value) {
    isDragOver.value = true
  }
}

/** Clear drag-over visual state */
const handleDragLeave = (e) => {
  isDragOver.value = false
}

/** Handle files dropped onto the upload zone */
const handleDrop = (e) => {
  isDragOver.value = false
  if (loading.value) return
  
  const droppedFiles = Array.from(e.dataTransfer.files)
  addFiles(droppedFiles)
}

/**
 * Validate and add new files to the file list.
 * Only accepts .pdf, .md, and .txt extensions.
 * @param {File[]} newFiles - Files to add
 */
const addFiles = (newFiles) => {
  const validFiles = newFiles.filter(file => {
    const ext = file.name.split('.').pop().toLowerCase()
    return ['pdf', 'md', 'txt'].includes(ext)
  })
  files.value.push(...validFiles)
}

/** Remove a file from the list by index */
const removeFile = (index) => {
  files.value.splice(index, 1)
}

// ─── Navigation & Submission ──────────────────────────────────────────────────

/** Smooth-scroll to the bottom of the page */
const scrollToBottom = () => {
  window.scrollTo({
    top: document.body.scrollHeight,
    behavior: 'smooth'
  })
}

/**
 * Start a new simulation: store files and requirements in the pending upload store,
 * then navigate to the Process page. The actual API call happens on the Process page.
 */
const startSimulation = () => {
  if (!canSubmit.value || loading.value) return
  
  // Store the data pending upload
  import('../store/pendingUpload.js').then(({ setPendingUpload }) => {
    setPendingUpload(files.value, formData.value.simulationRequirement)
    
    // Navigate immediately to the Process page (using a special identifier for a new project)
    router.push({
      name: 'Process',
      params: { projectId: 'new' }
    })
  })
}
</script>

<style scoped>
/* Global variables and reset */
:root {
  --black: #000000;
  --white: #FFFFFF;
  --orange: #FF4500;
  --gray-light: #F5F5F5;
  --gray-text: #666666;
  --border: #E5E5E5;
  /* 
    Use Space Grotesk as the primary heading font, JetBrains Mono as the code/label font
    Make sure these Google Fonts are imported in index.html
  */
  --font-mono: 'JetBrains Mono', monospace;
  --font-sans: 'Space Grotesk', 'Noto Sans SC', system-ui, sans-serif;
  --font-cn: 'Noto Sans SC', system-ui, sans-serif;
}

.home-container {
  min-height: 100vh;
  background: var(--white);
  font-family: var(--font-sans);
  color: var(--black);
}

/* Top navigation */
.navbar {
  height: 60px;
  background: var(--black);
  color: var(--white);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 40px;
}

.nav-brand {
  font-family: var(--font-mono);
  font-weight: 800;
  letter-spacing: 1px;
  font-size: 1.2rem;
}

.nav-links {
  display: flex;
  align-items: center;
}

.github-link {
  color: var(--white);
  text-decoration: none;
  font-family: var(--font-mono);
  font-size: 0.9rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: opacity 0.2s;
}

.github-link:hover {
  opacity: 0.8;
}

.arrow {
  font-family: sans-serif;
}

/* Main content area */
.main-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 60px 40px;
}

/* Hero section */
.hero-section {
  display: flex;
  justify-content: space-between;
  margin-bottom: 80px;
  position: relative;
}

.hero-left {
  flex: 1;
  padding-right: 60px;
}

.tag-row {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 25px;
  font-family: var(--font-mono);
  font-size: 0.8rem;
}

.orange-tag {
  background: var(--orange);
  color: var(--white);
  padding: 4px 10px;
  font-weight: 700;
  letter-spacing: 1px;
  font-size: 0.75rem;
}

.version-text {
  color: #999;
  font-weight: 500;
  letter-spacing: 0.5px;
}

.main-title {
  font-size: 4.5rem;
  line-height: 1.2;
  font-weight: 500;
  margin: 0 0 40px 0;
  letter-spacing: -2px;
  color: var(--black);
}

.gradient-text {
  background: linear-gradient(90deg, #000000 0%, #444444 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  display: inline-block;
}

.hero-desc {
  font-size: 1.05rem;
  line-height: 1.8;
  color: var(--gray-text);
  max-width: 640px;
  margin-bottom: 50px;
  font-weight: 400;
  text-align: justify;
}

.hero-desc p {
  margin-bottom: 1.5rem;
}

.highlight-bold {
  color: var(--black);
  font-weight: 700;
}

.highlight-orange {
  color: var(--orange);
  font-weight: 700;
  font-family: var(--font-mono);
}

.highlight-code {
  background: rgba(0, 0, 0, 0.05);
  padding: 2px 6px;
  border-radius: 2px;
  font-family: var(--font-mono);
  font-size: 0.9em;
  color: var(--black);
  font-weight: 600;
}

.slogan-text {
  font-size: 1.2rem;
  font-weight: 520;
  color: var(--black);
  letter-spacing: 1px;
  border-left: 3px solid var(--orange);
  padding-left: 15px;
  margin-top: 20px;
}

.blinking-cursor {
  color: var(--orange);
  animation: blink 1s step-end infinite;
  font-weight: 700;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.decoration-square {
  width: 16px;
  height: 16px;
  background: var(--orange);
}

.hero-right {
  flex: 0.8;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: flex-end;
}

.logo-container {
  width: 100%;
  display: flex;
  justify-content: flex-end;
  padding-right: 40px;
}

.hero-logo {
  max-width: 500px; /* Adjust logo size */
  width: 100%;
}

.scroll-down-btn {
  width: 40px;
  height: 40px;
  border: 1px solid var(--border);
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--orange);
  font-size: 1.2rem;
  transition: all 0.2s;
}

.scroll-down-btn:hover {
  border-color: var(--orange);
}

/* Dashboard two-column layout */
.dashboard-section {
  display: flex;
  gap: 60px;
  border-top: 1px solid var(--border);
  padding-top: 60px;
  align-items: flex-start;
}

.dashboard-section .left-panel,
.dashboard-section .right-panel {
  display: flex;
  flex-direction: column;
}

/* Left panel */
.left-panel {
  flex: 0.8;
}

.panel-header {
  font-family: var(--font-mono);
  font-size: 0.8rem;
  color: #999;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
}

.status-dot {
  color: var(--orange);
  font-size: 0.8rem;
}

.section-title {
  font-size: 2rem;
  font-weight: 520;
  margin: 0 0 15px 0;
}

.section-desc {
  color: var(--gray-text);
  margin-bottom: 25px;
  line-height: 1.6;
}

.metrics-row {
  display: flex;
  gap: 20px;
  margin-bottom: 15px;
}

.metric-card {
  border: 1px solid var(--border);
  padding: 20px 30px;
  min-width: 150px;
}

.metric-value {
  font-family: var(--font-mono);
  font-size: 1.8rem;
  font-weight: 520;
  margin-bottom: 5px;
}

.metric-label {
  font-size: 0.85rem;
  color: #999;
}

/* Project simulation steps introduction */
.steps-container {
  border: 1px solid var(--border);
  padding: 30px;
  position: relative;
}

.steps-header {
  font-family: var(--font-mono);
  font-size: 0.8rem;
  color: #999;
  margin-bottom: 25px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.diamond-icon {
  font-size: 1.2rem;
  line-height: 1;
}

.workflow-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.workflow-item {
  display: flex;
  align-items: flex-start;
  gap: 20px;
}

.step-num {
  font-family: var(--font-mono);
  font-weight: 700;
  color: var(--black);
  opacity: 0.3;
}

.step-info {
  flex: 1;
}

.step-title {
  font-weight: 520;
  font-size: 1rem;
  margin-bottom: 4px;
}

.step-desc {
  font-size: 0.85rem;
  color: var(--gray-text);
}

/* Right-side interactive console */
.right-panel {
  flex: 1.2;
}

.console-box {
  border: 1px solid #CCC; /* Outer solid border */
  padding: 8px; /* Inner padding to create a double-border effect */
}

.console-section {
  padding: 20px;
}

.console-section.btn-section {
  padding-top: 0;
}

.console-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 15px;
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: #666;
}

.upload-zone {
  border: 1px dashed #CCC;
  height: 200px;
  overflow-y: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
  background: #FAFAFA;
}

.upload-zone.has-files {
  align-items: flex-start;
}

.upload-zone:hover {
  background: #F0F0F0;
  border-color: #999;
}

.upload-placeholder {
  text-align: center;
}

.upload-icon {
  width: 40px;
  height: 40px;
  border: 1px solid #DDD;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 15px;
  color: #999;
}

.upload-title {
  font-weight: 500;
  font-size: 0.9rem;
  margin-bottom: 5px;
}

.upload-hint {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: #999;
}

.file-list {
  width: 100%;
  padding: 15px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.file-item {
  display: flex;
  align-items: center;
  background: var(--white);
  padding: 8px 12px;
  border: 1px solid #EEE;
  font-family: var(--font-mono);
  font-size: 0.85rem;
}

.file-name {
  flex: 1;
  margin: 0 10px;
}

.remove-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.2rem;
  color: #999;
}

.console-divider {
  display: flex;
  align-items: center;
  margin: 10px 0;
}

.console-divider::before,
.console-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: #EEE;
}

.console-divider span {
  padding: 0 15px;
  font-family: var(--font-mono);
  font-size: 0.7rem;
  color: #BBB;
  letter-spacing: 1px;
}

.input-wrapper {
  position: relative;
  border: 1px solid #DDD;
  background: #FAFAFA;
}

.code-input {
  width: 100%;
  border: none;
  background: transparent;
  padding: 20px;
  font-family: var(--font-mono);
  font-size: 0.9rem;
  line-height: 1.6;
  resize: vertical;
  outline: none;
  min-height: 150px;
}

.model-badge {
  position: absolute;
  bottom: 10px;
  right: 15px;
  font-family: var(--font-mono);
  font-size: 0.7rem;
  color: #AAA;
}

.start-engine-btn {
  width: 100%;
  background: var(--black);
  color: var(--white);
  border: none;
  padding: 20px;
  font-family: var(--font-mono);
  font-weight: 700;
  font-size: 1.1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  transition: all 0.3s ease;
  letter-spacing: 1px;
  position: relative;
  overflow: hidden;
}

/* Clickable state (not disabled) */
.start-engine-btn:not(:disabled) {
  background: var(--black);
  border: 1px solid var(--black);
  animation: pulse-border 2s infinite;
}

.start-engine-btn:hover:not(:disabled) {
  background: var(--orange);
  border-color: var(--orange);
  transform: translateY(-2px);
}

.start-engine-btn:active:not(:disabled) {
  transform: translateY(0);
}

.start-engine-btn:disabled {
  background: #E5E5E5;
  color: #999;
  cursor: not-allowed;
  transform: none;
  border: 1px solid #E5E5E5;
}

/* Guide animation: subtle border pulse */
@keyframes pulse-border {
  0% { box-shadow: 0 0 0 0 rgba(0, 0, 0, 0.2); }
  70% { box-shadow: 0 0 0 6px rgba(0, 0, 0, 0); }
  100% { box-shadow: 0 0 0 0 rgba(0, 0, 0, 0); }
}

/* {{ $t('home.quickTest.button') }} Section */
.quick-test-section {
  border-top: 1px solid var(--border);
  padding-top: 40px;
  margin-bottom: 40px;
}

.quick-test-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 24px;
  font-family: var(--font-mono);
}

.quick-test-label {
  font-weight: 700;
  font-size: 1rem;
}

.quick-test-subtitle {
  font-size: 0.8rem;
  color: #999;
}

.template-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}

.template-card {
  border: 1px solid var(--border);
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.template-card:hover {
  border-color: var(--orange);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}

.card-icon {
  font-size: 1.6rem;
  flex-shrink: 0;
}

.card-text {
  flex: 1;
  min-width: 0;
}

.card-title {
  font-family: var(--font-mono);
  font-weight: 700;
  font-size: 0.85rem;
  margin-bottom: 4px;
}

.card-subtitle {
  font-size: 0.8rem;
  color: var(--gray-text);
}

.card-arrow {
  font-size: 1.2rem;
  color: #ccc;
  flex-shrink: 0;
  transition: color 0.2s;
}

.template-card:hover .card-arrow {
  color: var(--orange);
}

/* Business Plan Section */
.business-plan-section {
  border-top: 1px solid var(--border);
  margin-top: 0;
}

.bp-dot {
  color: #10b981;
}

.business-plan-card {
  border-left: 3px solid #10b981;
}

.business-plan-card:hover {
  border-color: #10b981;
}

.business-plan-card:hover .card-arrow {
  color: #10b981;
}

/* Responsive */
@media (max-width: 1024px) {
  .dashboard-section {
    flex-direction: column;
  }

  .hero-section {
    flex-direction: column;
  }

  .hero-left {
    padding-right: 0;
    margin-bottom: 40px;
  }

  .hero-logo {
    max-width: 200px;
    margin-bottom: 20px;
  }

  .template-cards {
    grid-template-columns: 1fr;
  }
}
</style>
