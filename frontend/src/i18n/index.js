/**
 * Internationalization (i18n) configuration — MiroFish
 *
 * Uses vue-i18n in Composition API mode (legacy: false).
 * Supported locales: English (en) and Italian (it).
 * The selected locale is persisted in localStorage under 'mirofish-locale'.
 */
import { createI18n } from 'vue-i18n';
import en from './en.json';
import it from './it.json';

// Restore previously saved locale, default to English
const savedLocale = localStorage.getItem('mirofish-locale') || 'en';

const i18n = createI18n({
  legacy: false,
  locale: savedLocale,
  fallbackLocale: 'en',
  messages: {
    en,
    it
  }
});

/**
 * Switch the active locale and persist the choice.
 * Also updates the <html lang="..."> attribute for accessibility.
 * @param {'en'|'it'} locale - The locale code to activate
 */
export function setLocale(locale) {
  i18n.global.locale.value = locale;
  localStorage.setItem('mirofish-locale', locale);
  document.documentElement.setAttribute('lang', locale);
}

/**
 * Get the currently active locale code.
 * @returns {'en'|'it'} The active locale
 */
export function getLocale() {
  return i18n.global.locale.value;
}

export default i18n;
