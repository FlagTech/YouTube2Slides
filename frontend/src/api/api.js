import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getVideoInfo = async (url) => {
  const response = await api.post('/api/video/info', { url });
  return response.data;
};

export const processVideo = async (videoData) => {
  const response = await api.post('/api/video/process', videoData);
  return response.data;
};

export const getJobStatus = async (jobId) => {
  const response = await api.get(`/api/jobs/${jobId}`);
  return response.data;
};

export const translateText = async (text, sourceLang, targetLang) => {
  const response = await api.post('/api/translate', {
    text,
    source_lang: sourceLang,
    target_lang: targetLang,
  });
  return response.data;
};

export const getSupportedLanguages = async () => {
  const response = await api.get('/api/languages');
  return response.data;
};

export const deleteVideo = async (videoId) => {
  const response = await api.delete(`/api/video/${videoId}`);
  return response.data;
};

export const getVideoHistory = async () => {
  const response = await api.get('/api/videos/history');
  return response.data;
};

export default api;
