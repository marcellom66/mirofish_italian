<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-container">
      <div class="modal-header">
        <div class="modal-title-row">
          <span class="template-icon">{{ template.icon }}</span>
          <h2 class="modal-title">{{ t(template.titleKey) }}</h2>
        </div>
        <button class="close-btn" @click="$emit('close')">&times;</button>
      </div>

      <p class="modal-subtitle">{{ t(template.subtitleKey) }}</p>

      <div class="modal-body">
        <label class="input-label">{{ $t('quickTest.modal.describeIdea') }}</label>
        <textarea
          v-model="userInput"
          class="modal-textarea"
          :placeholder="t(template.placeholderKey)"
          rows="6"
        ></textarea>

        <div class="file-upload-section">
          <label class="input-label">{{ $t('quickTest.modal.attachFiles') }}</label>
          <div
            class="upload-zone"
            :class="{ 'drag-over': isDragOver }"
            @dragover.prevent="isDragOver = true"
            @dragleave.prevent="isDragOver = false"
            @drop.prevent="handleDrop"
            @click="$refs.fileInput.click()"
          >
            <input
              ref="fileInput"
              type="file"
              multiple
              accept=".pdf,.md,.txt"
              @change="handleFileSelect"
              style="display: none"
            />
            <div v-if="files.length === 0" class="upload-placeholder">
              <span class="upload-icon-arrow">&uarr;</span>
              <span>{{ $t('quickTest.modal.dragDropBrowse') }}</span>
            </div>
            <div v-else class="file-list">
              <div v-for="(file, i) in files" :key="i" class="file-item">
                <span class="file-name">{{ file.name }}</span>
                <button class="remove-btn" @click.stop="files.splice(i, 1)">&times;</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button class="cancel-btn" @click="$emit('close')">{{ $t('quickTest.modal.cancel') }}</button>
        <button class="launch-btn" :disabled="!userInput.trim()" @click="launch">
          {{ $t('quickTest.modal.launch') }} {{ $t('quickTest.title') }} <span class="btn-arrow">&rarr;</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * QuickTestModal.vue — Template-based quick simulation launcher
 *
 * Allows users to describe an idea in natural language, optionally attach files,
 * and launch a pre-configured simulation using a quick-test template.
 *
 * Props:
 *   @prop {Object} template - The quick-test template configuration (icon, titleKey, promptTemplate, etc.)
 *
 * Emits:
 *   @emit {void} close - When the user cancels or the modal is dismissed
 *
 * On launch:
 *   1. Creates a virtual seed file from the user input + template prefix
 *   2. Builds the simulation requirement using the template's promptTemplate function
 *   3. Stores everything via setPendingUpload and navigates to the Process page
 */
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { setPendingUpload } from '../store/pendingUpload'

const props = defineProps({
  template: { type: Object, required: true }
})
const emit = defineEmits(['close'])
const router = useRouter()
const { t } = useI18n()

/** @type {import('vue').Ref<string>} User's natural language description of their idea */
const userInput = ref('')
/** @type {import('vue').Ref<File[]>} Additional files attached by the user */
const files = ref([])
/** @type {import('vue').Ref<boolean>} Whether files are being dragged over the upload zone */
const isDragOver = ref(false)

/** Handle files selected via the native file picker (validates extensions) */
const handleFileSelect = (e) => {
  const selected = Array.from(e.target.files).filter(f => {
    const ext = f.name.split('.').pop().toLowerCase()
    return ['pdf', 'md', 'txt'].includes(ext)
  })
  files.value.push(...selected)
}

/** Handle files dropped onto the upload zone (validates extensions) */
const handleDrop = (e) => {
  isDragOver.value = false
  const dropped = Array.from(e.dataTransfer.files).filter(f => {
    const ext = f.name.split('.').pop().toLowerCase()
    return ['pdf', 'md', 'txt'].includes(ext)
  })
  files.value.push(...dropped)
}

/**
 * Launch the quick-test simulation:
 * - Creates a virtual seed file combining template prefix + user input
 * - Builds the simulation requirement from the template's prompt function
 * - Stores template config for later evaluation
 * - Navigates to the Process page
 */
const launch = () => {
  if (!userInput.value.trim()) return

  const seedText = props.template.seedPrefix + userInput.value
  const virtualFile = new File([seedText], 'quick_test_seed.txt', { type: 'text/plain' })
  const allFiles = [virtualFile, ...files.value]
  const requirement = props.template.promptTemplate(userInput.value)

  const templateConfig = {
    id: props.template.id,
    title: t(props.template.titleKey),
    userInput: userInput.value,
    evaluationPrompt: props.template.evaluationPrompt(userInput.value)
  }

  setPendingUpload(allFiles, requirement, props.template.id, templateConfig)

  emit('close')
  router.push({ name: 'Process', params: { projectId: 'new' } })
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-container {
  background: #fff;
  width: 580px;
  max-width: 90vw;
  max-height: 85vh;
  overflow-y: auto;
  border: 1px solid #e5e5e5;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 28px 0;
}

.modal-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.template-icon {
  font-size: 1.6rem;
}

.modal-title {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.2rem;
  font-weight: 700;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.6rem;
  cursor: pointer;
  color: #999;
  padding: 0 4px;
}

.modal-subtitle {
  padding: 8px 28px 0;
  color: #666;
  font-size: 0.9rem;
}

.modal-body {
  padding: 20px 28px;
}

.input-label {
  display: block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #999;
  margin-bottom: 8px;
  letter-spacing: 0.5px;
}

.modal-textarea {
  width: 100%;
  border: 1px solid #ddd;
  background: #fafafa;
  padding: 16px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.9rem;
  line-height: 1.6;
  resize: vertical;
  outline: none;
  box-sizing: border-box;
}

.modal-textarea:focus {
  border-color: #999;
}

.file-upload-section {
  margin-top: 20px;
}

.upload-zone {
  border: 1px dashed #ccc;
  padding: 16px;
  text-align: center;
  cursor: pointer;
  background: #fafafa;
  transition: all 0.2s;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  color: #999;
}

.upload-zone:hover,
.upload-zone.drag-over {
  background: #f0f0f0;
  border-color: #999;
}

.upload-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.upload-icon-arrow {
  font-size: 1rem;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
  padding: 6px 10px;
  border: 1px solid #eee;
  font-size: 0.8rem;
  color: #333;
}

.remove-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: #999;
  font-size: 1.1rem;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 0 28px 24px;
}

.cancel-btn {
  background: none;
  border: 1px solid #ddd;
  padding: 12px 24px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  cursor: pointer;
  color: #666;
}

.cancel-btn:hover {
  border-color: #999;
}

.launch-btn {
  background: #000;
  color: #fff;
  border: none;
  padding: 12px 28px;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  font-size: 0.85rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background 0.2s;
}

.launch-btn:hover:not(:disabled) {
  background: #FF4500;
}

.launch-btn:disabled {
  background: #e5e5e5;
  color: #999;
  cursor: not-allowed;
}

.btn-arrow {
  font-size: 1rem;
}
</style>
