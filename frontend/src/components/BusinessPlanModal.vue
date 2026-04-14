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

      <div class="step-indicator">
        {{ currentStep === 1 ? t('businessPlan.modal.step1Title') : t('businessPlan.modal.step2Title') }}
        <span class="step-counter">{{ currentStep }}/2</span>
      </div>

      <!-- Step 1: Company Profile -->
      <div v-if="currentStep === 1" class="modal-body">
        <div class="field-group">
          <label class="input-label">{{ t('businessPlan.modal.fields.sector') }}</label>
          <input
            v-model="metadata.sector"
            type="text"
            class="modal-input"
            :placeholder="t('businessPlan.modal.fields.sector')"
          />
        </div>

        <div class="field-group">
          <label class="input-label">{{ t('businessPlan.modal.fields.phase') }}</label>
          <select v-model="metadata.phase" class="modal-select">
            <option value="startup">{{ t('businessPlan.modal.phases.startup') }}</option>
            <option value="growth">{{ t('businessPlan.modal.phases.growth') }}</option>
            <option value="mature">{{ t('businessPlan.modal.phases.mature') }}</option>
            <option value="exit">{{ t('businessPlan.modal.phases.exit') }}</option>
          </select>
        </div>

        <div class="field-group">
          <label class="input-label">{{ t('businessPlan.modal.fields.targetMarket') }}</label>
          <input
            v-model="metadata.target_market"
            type="text"
            class="modal-input"
            :placeholder="t('businessPlan.modal.fields.targetMarket')"
          />
        </div>

        <div class="field-group">
          <label class="input-label">{{ t('businessPlan.modal.fields.budget') }}</label>
          <input
            v-model="metadata.budget"
            type="text"
            class="modal-input"
            :placeholder="t('businessPlan.modal.fields.budget')"
          />
        </div>

        <div class="field-group">
          <label class="input-label">{{ t('businessPlan.modal.fields.competitors') }}</label>
          <textarea
            v-model="metadata.competitors"
            class="modal-textarea"
            :placeholder="t('businessPlan.modal.fields.competitors')"
            rows="3"
          ></textarea>
        </div>

        <div class="field-group">
          <label class="input-label">{{ t('businessPlan.modal.fields.kpis') }}</label>
          <div class="checkbox-pill-group">
            <label
              v-for="kpi in ['revenue', 'marketShare', 'retention', 'cac', 'nps', 'ebitda']"
              :key="kpi"
              class="checkbox-pill"
              :class="{ active: metadata.kpis.includes(kpi) }"
            >
              <input type="checkbox" :value="kpi" v-model="metadata.kpis" />
              {{ t('businessPlan.modal.kpiOptions.' + kpi) }}
            </label>
          </div>
        </div>

        <div class="field-group">
          <label class="input-label">{{ t('businessPlan.modal.fields.riskAreas') }}</label>
          <div class="checkbox-pill-group">
            <label
              v-for="risk in ['market', 'financial', 'operational', 'regulatory', 'competitive']"
              :key="risk"
              class="checkbox-pill"
              :class="{ active: metadata.risk_areas.includes(risk) }"
            >
              <input type="checkbox" :value="risk" v-model="metadata.risk_areas" />
              {{ t('businessPlan.modal.riskOptions.' + risk) }}
            </label>
          </div>
        </div>

        <div class="field-group">
          <label class="input-label">{{ t('businessPlan.modal.fields.stakeholders') }}</label>
          <div class="checkbox-pill-group">
            <label
              v-for="stakeholder in ['investors', 'b2b', 'b2c', 'competitors', 'employees', 'media']"
              :key="stakeholder"
              class="checkbox-pill"
              :class="{ active: metadata.stakeholders.includes(stakeholder) }"
            >
              <input type="checkbox" :value="stakeholder" v-model="metadata.stakeholders" />
              {{ t('businessPlan.modal.stakeholderOptions.' + stakeholder) }}
            </label>
          </div>
        </div>

        <div class="field-group">
          <label class="input-label">{{ t('businessPlan.modal.fields.timeHorizon') }}</label>
          <select v-model="metadata.time_horizon" class="modal-select">
            <option value="6m">{{ t('businessPlan.modal.horizons.6m') }}</option>
            <option value="1y">{{ t('businessPlan.modal.horizons.1y') }}</option>
            <option value="3y">{{ t('businessPlan.modal.horizons.3y') }}</option>
            <option value="5y">{{ t('businessPlan.modal.horizons.5y') }}</option>
          </select>
        </div>
      </div>

      <!-- Step 2: Scenario & Documents -->
      <div v-if="currentStep === 2" class="modal-body">
        <div class="field-group">
          <label class="input-label">{{ t('businessPlan.modal.step2Title') }}</label>
          <textarea
            v-model="scenarioText"
            class="modal-textarea scenario-textarea"
            rows="8"
          ></textarea>
        </div>

        <div class="file-upload-section">
          <label class="input-label">{{ t('businessPlan.modal.fields.attachFiles') }}</label>
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
            <div v-if="attachedFiles.length === 0" class="upload-placeholder">
              <span class="upload-icon-arrow">&uarr;</span>
              <span>{{ $t('quickTest.modal.dragDropBrowse') }}</span>
            </div>
            <div v-else class="file-list">
              <div v-for="(file, i) in attachedFiles" :key="i" class="file-item">
                <span class="file-name">{{ file.name }}</span>
                <button class="remove-btn" @click.stop="attachedFiles.splice(i, 1)">&times;</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button class="cancel-btn" @click="$emit('close')">{{ $t('quickTest.modal.cancel') }}</button>
        <div class="footer-actions">
          <button v-if="currentStep === 2" class="back-btn" @click="currentStep = 1">
            {{ t('businessPlan.modal.back') }}
          </button>
          <button
            v-if="currentStep === 1"
            class="next-btn"
            :disabled="!metadata.sector.trim()"
            @click="currentStep = 2"
          >
            {{ t('businessPlan.modal.next') }} <span class="btn-arrow">&rarr;</span>
          </button>
          <button
            v-if="currentStep === 2"
            class="launch-btn"
            :disabled="isLoading"
            @click="launch"
          >
            {{ t('businessPlan.modal.launch') }} <span class="btn-arrow">&rarr;</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * BusinessPlanModal.vue — Two-step wizard for business plan simulation launcher
 *
 * Step 1: Collect company profile metadata (sector, phase, KPIs, risk areas, etc.)
 * Step 2: Review/edit auto-generated scenario prompt and optionally attach documents
 *
 * Props:
 *   @prop {Object} template - The business plan template (type: 'business_plan', has promptTemplate fn)
 *   @prop {Boolean} isOpen - Whether the modal is visible
 *
 * Emits:
 *   @emit {void} close - When the user cancels or dismisses the modal
 *
 * On launch:
 *   1. Builds computedMetadata from reactive fields (splitting competitors textarea by newline)
 *   2. Creates a virtual seed file from template.seedPrefix + scenarioText
 *   3. Calls setPendingUpload with all files and metadata
 *   4. Navigates to /process/new
 */
import { ref, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { setPendingUpload } from '../store/pendingUpload'

const props = defineProps({
  template: { type: Object, required: true },
  isOpen: { type: Boolean, default: false }
})
const emit = defineEmits(['close'])
const router = useRouter()
const { t } = useI18n()

/** Current wizard step (1 or 2) */
const currentStep = ref(1)

/** Company profile metadata collected in step 1 */
const metadata = reactive({
  sector: '',
  phase: 'startup',
  target_market: '',
  budget: '',
  competitors: '',
  kpis: [],
  risk_areas: [],
  stakeholders: [],
  time_horizon: '1y'
})

/** Editable scenario prompt, auto-populated from template.promptTemplate(metadata) */
const scenarioText = ref('')

/** Additional files attached by the user in step 2 */
const attachedFiles = ref([])

/** Whether files are being dragged over the upload zone */
const isDragOver = ref(false)

/** Whether the launch is in progress */
const isLoading = ref(false)

/** Build a metadata object suitable for promptTemplate, converting raw fields */
const buildComputedMetadata = () => ({
  ...metadata,
  competitors: metadata.competitors
    .split('\n')
    .map(s => s.trim())
    .filter(Boolean),
  stakeholders: metadata.stakeholders.join(', ')
})

/** Reset all state back to initial values */
const resetState = () => {
  currentStep.value = 1
  metadata.sector = ''
  metadata.phase = 'startup'
  metadata.target_market = ''
  metadata.budget = ''
  metadata.competitors = ''
  metadata.kpis = []
  metadata.risk_areas = []
  metadata.stakeholders = []
  metadata.time_horizon = '1y'
  scenarioText.value = ''
  attachedFiles.value = []
  isDragOver.value = false
  isLoading.value = false
}

/** Auto-update scenarioText when metadata changes (deep watch) */
watch(
  () => ({ ...metadata }),
  () => {
    scenarioText.value = props.template.promptTemplate(buildComputedMetadata())
  },
  { deep: true }
)

/** Reset state when modal is closed or template changes */
watch(() => props.isOpen, (newVal) => {
  if (!newVal) resetState()
})
watch(() => props.template, () => {
  resetState()
})

/** Handle files selected via the native file picker */
const handleFileSelect = (e) => {
  const selected = Array.from(e.target.files).filter(f => {
    const ext = f.name.split('.').pop().toLowerCase()
    return ['pdf', 'md', 'txt'].includes(ext)
  })
  attachedFiles.value.push(...selected)
}

/** Handle files dropped onto the upload zone */
const handleDrop = (e) => {
  isDragOver.value = false
  const dropped = Array.from(e.dataTransfer.files).filter(f => {
    const ext = f.name.split('.').pop().toLowerCase()
    return ['pdf', 'md', 'txt'].includes(ext)
  })
  attachedFiles.value.push(...dropped)
}

/**
 * Launch the business plan simulation:
 * - Builds computedMetadata with normalized competitors/stakeholders
 * - Creates a virtual seed file from template prefix + scenarioText
 * - Stores pending upload and navigates to the Process page
 */
const launch = () => {
  if (isLoading.value) return
  isLoading.value = true

  const computedMetadata = buildComputedMetadata()
  const simulationRequirement = scenarioText.value

  const seedText = props.template.seedPrefix + scenarioText.value
  const seedFile = new File([seedText], 'business_plan_seed.txt', { type: 'text/plain' })
  const allFiles = [seedFile, ...attachedFiles.value]

  setPendingUpload(allFiles, simulationRequirement, props.template.id, props.template, computedMetadata)

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
  width: 620px;
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

.step-indicator {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 28px;
  background: #f0fdf8;
  border-top: 1px solid #d1fae5;
  border-bottom: 1px solid #d1fae5;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  font-weight: 600;
  color: #059669;
  margin-top: 12px;
}

.step-counter {
  font-size: 0.75rem;
  color: #10b981;
  background: #d1fae5;
  padding: 2px 8px;
  border-radius: 10px;
}

.modal-body {
  padding: 20px 28px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.input-label {
  display: block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #999;
  letter-spacing: 0.5px;
}

.modal-input {
  width: 100%;
  border: 1px solid #ddd;
  background: #fafafa;
  padding: 10px 14px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.9rem;
  outline: none;
  box-sizing: border-box;
}

.modal-input:focus {
  border-color: #10b981;
}

.modal-select {
  width: 100%;
  border: 1px solid #ddd;
  background: #fafafa;
  padding: 10px 14px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.9rem;
  outline: none;
  box-sizing: border-box;
  cursor: pointer;
  appearance: auto;
}

.modal-select:focus {
  border-color: #10b981;
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
  border-color: #10b981;
}

.scenario-textarea {
  min-height: 180px;
}

/* Checkbox pill groups */
.checkbox-pill-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.checkbox-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border: 1px solid #ddd;
  background: #fafafa;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.78rem;
  cursor: pointer;
  transition: all 0.15s;
  user-select: none;
}

.checkbox-pill input[type="checkbox"] {
  display: none;
}

.checkbox-pill:hover {
  border-color: #10b981;
  background: #f0fdf8;
}

.checkbox-pill.active {
  border-color: #10b981;
  background: #d1fae5;
  color: #059669;
  font-weight: 600;
}

/* File upload section */
.file-upload-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
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
  background: #f0fdf8;
  border-color: #10b981;
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
  text-align: left;
}

.file-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.remove-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: #999;
  font-size: 1.1rem;
}

/* Footer */
.modal-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 0 28px 24px;
}

.footer-actions {
  display: flex;
  gap: 10px;
  align-items: center;
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

.back-btn {
  background: none;
  border: 1px solid #ddd;
  padding: 12px 24px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  cursor: pointer;
  color: #666;
}

.back-btn:hover {
  border-color: #10b981;
  color: #10b981;
}

.next-btn {
  background: #10b981;
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

.next-btn:hover:not(:disabled) {
  background: #059669;
}

.next-btn:disabled {
  background: #e5e5e5;
  color: #999;
  cursor: not-allowed;
}

.launch-btn {
  background: #10b981;
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
  background: #059669;
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
