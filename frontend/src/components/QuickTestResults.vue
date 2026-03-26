<template>
  <div class="quick-test-results">
    <div class="results-header">
      <div class="header-left">
        <span class="header-deco">&#x25C6;</span>
        <span class="header-title">{{ $t('quickTest.results') }}</span>
      </div>
      <span class="header-meta">{{ $t('quickTest.resultsMeta', { count: totalAgents }) }}</span>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>{{ $t('quickTest.resultsLoading') }}</p>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button class="retry-btn" @click="$emit('retry')">{{ $t('quickTest.retry') }}</button>
    </div>

    <!-- Results -->
    <div v-else-if="analysisData" class="results-content">
      <!-- Overall Verdict: Pie Chart -->
      <div class="result-section">
        <h3 class="section-title">{{ $t('quickTest.overallVerdict') }}</h3>
        <div class="verdict-row">
          <div class="pie-chart-container">
            <svg ref="pieSvg" width="220" height="220"></svg>
          </div>
          <div class="verdict-legend">
            <div class="legend-item">
              <span class="legend-dot favorable"></span>
              <span class="legend-label">{{ $t('quickTest.favorable') }}</span>
              <span class="legend-value">{{ percentages.favorable }}%</span>
            </div>
            <div class="legend-item">
              <span class="legend-dot unfavorable"></span>
              <span class="legend-label">{{ $t('quickTest.unfavorable') }}</span>
              <span class="legend-value">{{ percentages.unfavorable }}%</span>
            </div>
            <div class="legend-item">
              <span class="legend-dot neutral"></span>
              <span class="legend-label">{{ $t('quickTest.neutral') }}</span>
              <span class="legend-value">{{ percentages.neutral }}%</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Sentiment Score -->
      <div class="result-section">
        <h3 class="section-title">{{ $t('quickTest.sentimentScore') }}</h3>
        <div class="sentiment-gauge">
          <div class="gauge-labels">
            <span>-10</span>
            <span>0</span>
            <span>+10</span>
          </div>
          <div class="gauge-bar">
            <div class="gauge-fill" :style="gaugeStyle"></div>
            <div class="gauge-marker" :style="markerStyle"></div>
          </div>
          <div class="gauge-value">{{ avgScore.toFixed(1) }}</div>
        </div>
      </div>

      <!-- Bar Chart: Breakdown by Category -->
      <div v-if="categoryData.length > 0" class="result-section">
        <h3 class="section-title">{{ $t('quickTest.breakdownByCategory') }}</h3>
        <svg ref="barSvg" class="bar-chart-svg"></svg>
      </div>

      <!-- Key Themes -->
      <div class="result-section">
        <h3 class="section-title">{{ $t('quickTest.keyThemes') }}</h3>
        <div class="themes-row">
          <div class="themes-column positive">
            <h4 class="themes-label">{{ $t('quickTest.topPositiveReasons') }}</h4>
            <ul class="themes-list">
              <li v-for="(theme, i) in topPositiveReasons" :key="'p'+i">{{ theme }}</li>
            </ul>
          </div>
          <div class="themes-column negative">
            <h4 class="themes-label">{{ $t('quickTest.topNegativeReasons') }}</h4>
            <ul class="themes-list">
              <li v-for="(theme, i) in topNegativeReasons" :key="'n'+i">{{ theme }}</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Expandable Raw Data -->
      <div class="result-section">
        <button class="toggle-raw-btn" @click="showRawData = !showRawData">
          {{ showRawData ? $t('quickTest.hide') : $t('quickTest.show') }} {{ $t('quickTest.individualResponses') }} ({{ analysisData.responses.length }})
        </button>
        <div v-if="showRawData" class="raw-data-table">
          <table>
            <thead>
              <tr>
                <th>{{ $t('quickTest.agent') }}</th>
                <th>{{ $t('quickTest.sentiment') }}</th>
                <th>{{ $t('quickTest.score') }}</th>
                <th>{{ $t('quickTest.reason') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(r, i) in analysisData.responses" :key="i">
                <td>{{ r.agentId || `${$t('quickTest.agent')} ${i + 1}` }}</td>
                <td>
                  <span class="sentiment-badge" :class="r.sentiment">{{ r.sentiment }}</span>
                </td>
                <td>{{ r.score }}</td>
                <td>{{ r.reason }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * QuickTestResults.vue — Quick-test analysis results dashboard
 *
 * Displays the results of a quick-test simulation analysis including:
 *   - Overall verdict pie chart (favorable/unfavorable/neutral distribution)
 *   - Sentiment score gauge (-10 to +10 scale)
 *   - Category breakdown bar chart (grouped by agent category)
 *   - Key themes: top positive and negative reasons
 *   - Expandable raw data table with individual agent responses
 *
 * Uses D3.js for SVG pie and bar chart rendering.
 *
 * Props:
 *   @prop {boolean} loading - Whether results are being fetched
 *   @prop {string|null} error - Error message if the request failed
 *   @prop {Object|null} analysisData - The analysis result object with responses array
 *
 * Emits:
 *   @emit {void} retry - When the user clicks the retry button on error
 */
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import * as d3 from 'd3'

const props = defineProps({
  loading: { type: Boolean, default: false },
  error: { type: String, default: null },
  analysisData: { type: Object, default: null }
})

defineEmits(['retry'])
const { t } = useI18n()

/** @type {import('vue').Ref<SVGSVGElement|null>} SVG element reference for the pie chart */
const pieSvg = ref(null)
/** @type {import('vue').Ref<SVGSVGElement|null>} SVG element reference for the bar chart */
const barSvg = ref(null)
/** @type {import('vue').Ref<boolean>} Whether the raw data table is expanded */
const showRawData = ref(false)

/** Total number of agent responses */
const totalAgents = computed(() => props.analysisData?.responses?.length || 0)

/** Count of responses by sentiment category */
const counts = computed(() => {
  if (!props.analysisData?.responses) return { favorable: 0, unfavorable: 0, neutral: 0 }
  const r = props.analysisData.responses
  return {
    favorable: r.filter(x => x.sentiment === 'favorable').length,
    unfavorable: r.filter(x => x.sentiment === 'unfavorable').length,
    neutral: r.filter(x => x.sentiment === 'neutral').length
  }
})

/** Percentage distribution of sentiments (rounded) */
const percentages = computed(() => {
  const t = totalAgents.value || 1
  return {
    favorable: Math.round((counts.value.favorable / t) * 100),
    unfavorable: Math.round((counts.value.unfavorable / t) * 100),
    neutral: Math.round((counts.value.neutral / t) * 100)
  }
})

/** Average sentiment score across all agent responses */
const avgScore = computed(() => {
  if (!props.analysisData?.responses?.length) return 0
  const scores = props.analysisData.responses.map(r => r.score).filter(s => typeof s === 'number')
  return scores.length ? scores.reduce((a, b) => a + b, 0) / scores.length : 0
})

/** CSS style for the sentiment gauge fill bar (maps -10..+10 to 0..100%) */
const gaugeStyle = computed(() => {
  const pct = ((avgScore.value + 10) / 20) * 100
  return { width: `${Math.max(0, Math.min(100, pct))}%` }
})

/** CSS style for the sentiment gauge marker position */
const markerStyle = computed(() => {
  const pct = ((avgScore.value + 10) / 20) * 100
  return { left: `${Math.max(0, Math.min(100, pct))}%` }
})

/** Group responses by category for the bar chart breakdown */
const categoryData = computed(() => {
  if (!props.analysisData?.responses) return []
  const groups = {}
  for (const r of props.analysisData.responses) {
    const cat = r.category || t('quickTest.unknown')
    if (!groups[cat]) groups[cat] = { favorable: 0, unfavorable: 0, neutral: 0 }
    if (r.sentiment in groups[cat]) groups[cat][r.sentiment]++
  }
  return Object.entries(groups).map(([name, vals]) => ({ name, ...vals }))
})

/** Top 5 positive reasons from favorable responses */
const topPositiveReasons = computed(() => {
  if (!props.analysisData?.responses) return []
  return props.analysisData.responses
    .filter(r => r.sentiment === 'favorable' && r.reason)
    .slice(0, 5)
    .map(r => r.reason)
})

/** Top 5 negative reasons from unfavorable responses */
const topNegativeReasons = computed(() => {
  if (!props.analysisData?.responses) return []
  return props.analysisData.responses
    .filter(r => r.sentiment === 'unfavorable' && r.reason)
    .slice(0, 5)
    .map(r => r.reason)
})

/** Render the donut pie chart using D3.js (favorable/unfavorable/neutral) */
function drawPieChart() {
  if (!pieSvg.value || !props.analysisData) return
  const svg = d3.select(pieSvg.value)
  svg.selectAll('*').remove()

  const width = 220, height = 220, radius = 90
  const g = svg.append('g').attr('transform', `translate(${width / 2},${height / 2})`)

  const data = [
    { label: t('quickTest.favorable'), value: counts.value.favorable, color: '#22c55e' },
    { label: t('quickTest.unfavorable'), value: counts.value.unfavorable, color: '#ef4444' },
    { label: t('quickTest.neutral'), value: counts.value.neutral, color: '#9ca3af' }
  ].filter(d => d.value > 0)

  const pie = d3.pie().value(d => d.value).sort(null)
  const arc = d3.arc().innerRadius(45).outerRadius(radius)

  g.selectAll('path')
    .data(pie(data))
    .join('path')
    .attr('d', arc)
    .attr('fill', d => d.data.color)
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)

  g.selectAll('text')
    .data(pie(data))
    .join('text')
    .attr('transform', d => `translate(${arc.centroid(d)})`)
    .attr('text-anchor', 'middle')
    .attr('font-size', '12px')
    .attr('font-family', "'JetBrains Mono', monospace")
    .attr('fill', '#fff')
    .attr('font-weight', '700')
    .text(d => {
      const pct = Math.round((d.data.value / totalAgents.value) * 100)
      return pct > 5 ? `${pct}%` : ''
    })
}

/** Render the grouped bar chart using D3.js (sentiment counts per category) */
function drawBarChart() {
  if (!barSvg.value || !categoryData.value.length) return
  const svg = d3.select(barSvg.value)
  svg.selectAll('*').remove()

  const margin = { top: 20, right: 20, bottom: 60, left: 40 }
  const width = 500 - margin.left - margin.right
  const height = 250 - margin.top - margin.bottom

  svg.attr('width', width + margin.left + margin.right)
    .attr('height', height + margin.top + margin.bottom)

  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

  const categories = categoryData.value.map(d => d.name)
  const sentiments = ['favorable', 'unfavorable', 'neutral']
  const colors = { favorable: '#22c55e', unfavorable: '#ef4444', neutral: '#9ca3af' }

  const x0 = d3.scaleBand().domain(categories).range([0, width]).padding(0.2)
  const x1 = d3.scaleBand().domain(sentiments).range([0, x0.bandwidth()]).padding(0.05)
  const maxVal = d3.max(categoryData.value, d => Math.max(d.favorable, d.unfavorable, d.neutral)) || 1
  const y = d3.scaleLinear().domain([0, maxVal]).range([height, 0])

  // Bars
  const groups = g.selectAll('.category-group')
    .data(categoryData.value)
    .join('g')
    .attr('transform', d => `translate(${x0(d.name)},0)`)

  groups.selectAll('rect')
    .data(d => sentiments.map(s => ({ sentiment: s, value: d[s] })))
    .join('rect')
    .attr('x', d => x1(d.sentiment))
    .attr('y', d => y(d.value))
    .attr('width', x1.bandwidth())
    .attr('height', d => height - y(d.value))
    .attr('fill', d => colors[d.sentiment])

  // Axes
  g.append('g')
    .attr('transform', `translate(0,${height})`)
    .call(d3.axisBottom(x0))
    .selectAll('text')
    .attr('font-size', '10px')
    .attr('font-family', "'JetBrains Mono', monospace")
    .attr('transform', 'rotate(-25)')
    .attr('text-anchor', 'end')

  g.append('g')
    .call(d3.axisLeft(y).ticks(5))
    .selectAll('text')
    .attr('font-size', '10px')
    .attr('font-family', "'JetBrains Mono', monospace")
}

watch(() => props.analysisData, async () => {
  if (props.analysisData) {
    await nextTick()
    drawPieChart()
    drawBarChart()
  }
}, { immediate: true })

onMounted(() => {
  if (props.analysisData) {
    drawPieChart()
    drawBarChart()
  }
})
</script>

<style scoped>
.quick-test-results {
  border: 1px solid #e5e5e5;
  background: #fff;
  margin-bottom: 24px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid #e5e5e5;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-deco {
  color: #FF4500;
  font-size: 0.9rem;
}

.header-title {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  font-size: 1rem;
}

.header-meta {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #999;
}

.loading-state, .error-state {
  padding: 48px 24px;
  text-align: center;
  color: #666;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e5e5e5;
  border-top-color: #FF4500;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.retry-btn {
  margin-top: 12px;
  background: #000;
  color: #fff;
  border: none;
  padding: 8px 20px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  cursor: pointer;
}

.results-content {
  padding: 24px;
}

.result-section {
  margin-bottom: 32px;
}

.result-section:last-child {
  margin-bottom: 0;
}

.section-title {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  font-weight: 700;
  margin: 0 0 16px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid #eee;
}

/* Pie chart section */
.verdict-row {
  display: flex;
  align-items: center;
  gap: 32px;
}

.verdict-legend {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.legend-dot.favorable { background: #22c55e; }
.legend-dot.unfavorable { background: #ef4444; }
.legend-dot.neutral { background: #9ca3af; }

.legend-label { color: #666; min-width: 90px; }
.legend-value { font-weight: 700; color: #000; }

/* Sentiment gauge */
.sentiment-gauge {
  max-width: 400px;
}

.gauge-labels {
  display: flex;
  justify-content: space-between;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: #999;
  margin-bottom: 4px;
}

.gauge-bar {
  height: 12px;
  background: #f0f0f0;
  position: relative;
  border-radius: 2px;
  overflow: visible;
}

.gauge-fill {
  height: 100%;
  background: linear-gradient(90deg, #ef4444, #f59e0b, #22c55e);
  border-radius: 2px;
  transition: width 0.5s;
}

.gauge-marker {
  position: absolute;
  top: -4px;
  width: 3px;
  height: 20px;
  background: #000;
  transform: translateX(-50%);
  transition: left 0.5s;
}

.gauge-value {
  text-align: center;
  margin-top: 8px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.4rem;
  font-weight: 700;
}

/* Bar chart */
.bar-chart-svg {
  display: block;
  max-width: 100%;
}

/* Themes */
.themes-row {
  display: flex;
  gap: 24px;
}

.themes-column {
  flex: 1;
  padding: 16px;
  border: 1px solid #eee;
}

.themes-column.positive { border-left: 3px solid #22c55e; }
.themes-column.negative { border-left: 3px solid #ef4444; }

.themes-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #999;
  margin: 0 0 10px 0;
  font-weight: 600;
}

.themes-list {
  margin: 0;
  padding: 0 0 0 16px;
  font-size: 0.85rem;
  color: #333;
  line-height: 1.8;
}

/* Raw data table */
.toggle-raw-btn {
  background: none;
  border: 1px solid #ddd;
  padding: 8px 16px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  cursor: pointer;
  color: #666;
  width: 100%;
  text-align: left;
}

.toggle-raw-btn:hover {
  border-color: #999;
}

.raw-data-table {
  margin-top: 12px;
  overflow-x: auto;
}

.raw-data-table table {
  width: 100%;
  border-collapse: collapse;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
}

.raw-data-table th {
  background: #f5f5f5;
  padding: 8px 12px;
  text-align: left;
  font-weight: 600;
  border-bottom: 1px solid #ddd;
}

.raw-data-table td {
  padding: 8px 12px;
  border-bottom: 1px solid #eee;
}

.sentiment-badge {
  display: inline-block;
  padding: 2px 8px;
  font-size: 0.7rem;
  font-weight: 600;
  border-radius: 2px;
}

.sentiment-badge.favorable { background: #dcfce7; color: #166534; }
.sentiment-badge.unfavorable { background: #fee2e2; color: #991b1b; }
.sentiment-badge.neutral { background: #f3f4f6; color: #4b5563; }
</style>
