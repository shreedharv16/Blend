import axios from 'axios';
import type { ChatRequest, ChatResponse, FileInfo, DashboardData } from '../types';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const uploadFile = async (file: File): Promise<FileInfo> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post<FileInfo>('/upload/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

export const sendChatMessage = async (request: ChatRequest): Promise<ChatResponse> => {
  const response = await api.post<ChatResponse>('/chat/', request);
  return response.data;
};

export const getDashboard = async (fileId: string): Promise<DashboardData> => {
  const response = await api.get<DashboardData>(`/dashboard/${fileId}`);
  return response.data;
};

export const refreshDashboard = async (fileId: string): Promise<DashboardData> => {
  const response = await api.post<DashboardData>(`/dashboard/${fileId}/refresh`);
  return response.data;
};

export const getHealth = async (): Promise<any> => {
  const response = await api.get('/health');
  return response.data;
};

export default api;

