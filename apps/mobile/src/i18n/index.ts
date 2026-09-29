import * as Localization from 'expo-localization';
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import en from './locales/en.json';
import fr from './locales/fr.json';

// English only if the phone is set to English; French otherwise.
function deviceLanguage(): 'fr' | 'en' {
  const code = Localization.getLocales()[0]?.languageCode;
  return code === 'en' ? 'en' : 'fr';
}

i18n.use(initReactI18next).init({
  resources: { fr: { translation: fr }, en: { translation: en } },
  lng: deviceLanguage(),
  fallbackLng: 'fr',
  interpolation: { escapeValue: false },
  react: { useSuspense: false },
});

export default i18n;
