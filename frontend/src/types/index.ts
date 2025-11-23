export interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  data?: QueryData;
  visualizations?: Visualization[];
}

export interface QueryData {
  results: any[];
  count: number;
  sql?: string;
}

export interface Visualization {
  type: 'bar' | 'line' | 'pie' | 'area' | 'scatter' | 'table';
  title: string;
  data: any[];
  x_axis?: string;
  y_axis?: string;
  colors?: string[];
  height?: number;
}

export interface KPICard {
  title: string;
  value: any;
  unit?: string;
  change?: number;
  change_label?: string;
  trend?: 'up' | 'down' | 'neutral';
}

export interface ChartConfig {
  type: 'bar' | 'line' | 'pie' | 'area' | 'scatter' | 'table';
  title: string;
  data: any[];
  x_axis?: string;
  y_axis?: string;
  colors?: string[];
  height?: number;
}

export interface DashboardData {
  file_id: string;
  kpis: KPICard[];
  charts: ChartConfig[];
  generated_at: string;
}

export interface FileInfo {
  file_id: string;
  filename: string;
  size: number;
  row_count: number;
  column_count: number;
  columns: string[];
  preview: any[];
  summary?: string;
  processing_time: number;
}

export interface ChatRequest {
  message: string;
  file_id?: string;
  conversation_id?: string;
}

export interface ChatResponse {
  message: string;
  role: 'assistant';
  conversation_id: string;
  query_type?: string;
  data?: QueryData;
  visualizations?: Visualization[];
  processing_time: number;
}

