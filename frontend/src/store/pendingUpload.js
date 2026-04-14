/**
 * Pending Upload Store — MiroFish
 *
 * Reactive store that holds uploaded files and simulation requirements
 * between the QuickTest modal and the main process view.
 * Uses sessionStorage as a fallback to survive page reloads.
 */
import { reactive } from 'vue'

/** @type {{ files: File[], simulationRequirement: string, isPending: boolean, templateId: string|null, templateConfig: Object|null, business_plan_metadata: Object|null }} */
const state = reactive({
  files: [],
  simulationRequirement: '',
  isPending: false,
  templateId: null,
  templateConfig: null,
  business_plan_metadata: null
})

/**
 * Store a pending upload with optional quick-test template metadata.
 * Persists template info to sessionStorage for cross-page navigation.
 * @param {File[]} files - Uploaded document files
 * @param {string} requirement - Simulation requirement text
 * @param {string|null} [templateId=null] - Quick-test template identifier
 * @param {Object|null} [templateConfig=null] - Quick-test template configuration
 * @param {Object|null} [businessPlanMetadata=null] - Business plan metadata for project creation
 */
export function setPendingUpload(files, requirement, templateId = null, templateConfig = null, businessPlanMetadata = null) {
  state.files = files
  state.simulationRequirement = requirement
  state.isPending = true
  state.templateId = templateId
  state.templateConfig = templateConfig
  state.business_plan_metadata = businessPlanMetadata
  // Persist template data to sessionStorage for page-reload resilience
  if (templateId) {
    sessionStorage.setItem('quickTestTemplateId', templateId)
    sessionStorage.setItem('quickTestTemplateConfig', JSON.stringify(templateConfig))
  }
  if (businessPlanMetadata) {
    sessionStorage.setItem('businessPlanMetadata', JSON.stringify(businessPlanMetadata))
  }
}

/**
 * Retrieve the current pending upload state.
 * Falls back to sessionStorage if reactive state was lost (e.g. page reload).
 * @returns {{ files: File[], simulationRequirement: string, isPending: boolean, templateId: string|null, templateConfig: Object|null, business_plan_metadata: Object|null }}
 */
export function getPendingUpload() {
  const templateId = state.templateId || sessionStorage.getItem('quickTestTemplateId') || null
  let templateConfig = state.templateConfig
  if (!templateConfig && templateId) {
    try {
      templateConfig = JSON.parse(sessionStorage.getItem('quickTestTemplateConfig'))
    } catch { templateConfig = null }
  }
  let businessPlanMetadata = state.business_plan_metadata
  if (!businessPlanMetadata) {
    try {
      const stored = sessionStorage.getItem('businessPlanMetadata')
      businessPlanMetadata = stored ? JSON.parse(stored) : null
    } catch { businessPlanMetadata = null }
  }
  return {
    files: state.files,
    simulationRequirement: state.simulationRequirement,
    isPending: state.isPending,
    templateId,
    templateConfig,
    business_plan_metadata: businessPlanMetadata
  }
}

/**
 * Clear all pending upload data from both reactive state and sessionStorage.
 */
export function clearPendingUpload() {
  state.files = []
  state.simulationRequirement = ''
  state.isPending = false
  state.templateId = null
  state.templateConfig = null
  state.business_plan_metadata = null
  sessionStorage.removeItem('quickTestTemplateId')
  sessionStorage.removeItem('quickTestTemplateConfig')
  sessionStorage.removeItem('businessPlanMetadata')
}

export default state
