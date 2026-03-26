<template>
  <div class="language-selector">
    <button 
      class="lang-btn" 
      @click="toggleDropdown"
      :title="currentLang === 'en' ? 'Switch to Italian' : 'Passa a Inglese'"
    >
      <span class="flag">{{ currentLang === 'en' ? '🇬🇧' : '🇮🇹' }}</span>
      <span class="lang-code">{{ currentLang.toUpperCase() }}</span>
      <span class="arrow" :class="{ open: isOpen }">▼</span>
    </button>
    <div v-if="isOpen" class="dropdown">
      <button 
        class="dropdown-item" 
        :class="{ active: currentLang === 'en' }"
        @click="selectLanguage('en')"
      >
        <span class="flag">🇬🇧</span>
        <span>English</span>
      </button>
      <button 
        class="dropdown-item" 
        :class="{ active: currentLang === 'it' }"
        @click="selectLanguage('it')"
      >
        <span class="flag">🇮🇹</span>
        <span>Italiano</span>
      </button>
    </div>
  </div>
</template>

<script setup>
/**
 * LanguageSelector.vue — Floating locale switcher
 *
 * Displays a dropdown button to switch between English and Italian.
 * Persists the selected locale via the i18n module (localStorage).
 * Closes automatically when clicking outside the component.
 */
import { ref, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { setLocale, getLocale } from '../i18n';

const { locale } = useI18n();
const isOpen = ref(false);

/** Currently active locale code ('en' or 'it') */
const currentLang = computed(() => locale.value || getLocale());

/** Toggle the dropdown visibility */
function toggleDropdown() {
  isOpen.value = !isOpen.value;
}

/**
 * Select a language, update the i18n locale, and close the dropdown.
 * @param {'en'|'it'} lang - The locale code to switch to
 */
function selectLanguage(lang) {
  setLocale(lang);
  locale.value = lang;
  isOpen.value = false;
}

// Close dropdown when clicking outside the component
if (typeof window !== 'undefined') {
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.language-selector')) {
      isOpen.value = false;
    }
  });
}
</script>

<style scoped>
.language-selector {
  position: relative;
  display: inline-block;
}

.lang-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  color: #fff;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.lang-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.flag {
  font-size: 16px;
}

.lang-code {
  font-weight: 500;
}

.arrow {
  font-size: 10px;
  transition: transform 0.2s;
}

.arrow.open {
  transform: rotate(180deg);
}

.dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 4px;
  background: #1a1a2e;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  z-index: 1000;
  min-width: 140px;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 14px;
  background: none;
  border: none;
  color: #fff;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
  text-align: left;
}

.dropdown-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

.dropdown-item.active {
  background: rgba(79, 172, 254, 0.2);
  color: #4facfe;
}
</style>
