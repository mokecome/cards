import axios from 'axios';

const API_BASE_URL = '/api/v1';

// 創建axios實例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 請求攔截器
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 響應攔截器
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API錯誤:', error);
    return Promise.reject(error);
  }
);

// 名片相關API
export const getCards = () => api.get('/cards/');

export const getCard = (id) => api.get(`/cards/${id}`);

export const createCard = (cardData) => api.post('/cards/', cardData);

export const updateCard = (id, cardData) => api.put(`/cards/${id}`, cardData);

export const deleteCard = (id) => api.delete(`/cards/${id}`);

export const exportCards = (format = 'csv') => 
  api.get(`/cards/export/download?format=${format}`, {
    responseType: 'blob',
  });

// OCR相關API
export const ocrImage = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  return api.post('/ocr/image', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

export default api; 