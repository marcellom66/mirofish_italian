/**
 * MiroFish — Application entry point
 * Initializes the Vue 3 app with router and i18n plugins,
 * then mounts it to the #app DOM element.
 */
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import i18n from './i18n'

const app = createApp(App)

// Register plugins: client-side routing and internationalization
app.use(router)
app.use(i18n)

app.mount('#app')
