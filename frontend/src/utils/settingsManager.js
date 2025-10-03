/**
 * Settings Manager for localStorage operations
 */

const SETTINGS_KEY = 'videoConverterSettings';

export const saveSettings = (settings) => {
  try {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
    console.log('Settings saved:', settings);
    return true;
  } catch (error) {
    console.error('Failed to save settings:', error);
    return false;
  }
};

export const getSettings = () => {
  try {
    const savedSettings = localStorage.getItem(SETTINGS_KEY);
    if (savedSettings) {
      const parsed = JSON.parse(savedSettings);
      console.log('Settings loaded:', parsed);
      return parsed;
    }
    return null;
  } catch (error) {
    console.error('Failed to get settings:', error);
    return null;
  }
};

export const clearSettings = () => {
  try {
    localStorage.removeItem(SETTINGS_KEY);
    console.log('Settings cleared');
    return true;
  } catch (error) {
    console.error('Failed to clear settings:', error);
    return false;
  }
};

export const getDefaultSettings = () => {
  return {
    quality: '720',
    subtitleLanguages: ['zh-TW', 'en'],
    translateTo: '',
    generateOutline: false,
    aiProvider: 'openai',
    aiModel: 'gpt-4o-mini',
    apiKey: ''
  };
};
