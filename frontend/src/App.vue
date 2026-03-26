<template>
  <!-- Root view: renders the current route component -->
  <router-view />
  <!-- Floating language selector overlay -->
  <LanguageSelector />
</template>

<script setup>
/**
 * App.vue — Root application component
 * Renders the current route via <router-view> and displays
 * the floating LanguageSelector for locale switching.
 */
import LanguageSelector from './components/LanguageSelector.vue'
</script>

<style>
/* Global style reset */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: 'JetBrains Mono', 'Space Grotesk', 'Noto Sans SC', monospace;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #000000;
  background-color: #ffffff;
}

/* Scrollbar styles */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
}

::-webkit-scrollbar-thumb {
  background: #000000;
}

::-webkit-scrollbar-thumb:hover {
  background: #333333;
}

/* Global button styles */
button {
  font-family: inherit;
}
</style>
