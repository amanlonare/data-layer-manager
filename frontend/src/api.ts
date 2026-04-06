const API_BASE_URL = 'http://localhost:8000';
const API_KEY = 'dev-secret-key'; // For local dev, normally in .env

export interface SearchStrategyConfig {
  name: string;
  parameters?: Record<string, any>;
}

export interface SearchRequest {
  query: string;
  limit: number;
  strategy?: string | SearchStrategyConfig;
  rerank_threshold?: number;
}

export interface SearchResult {
  id: string;
  content: string;
  score: number;
  metadata: Record<string, any>;
}

export interface SearchResponse {
  results: SearchResult[];
}

export interface IngestRequest {
  content: string;
  metadata?: Record<string, any>;
  source?: string;
}

export interface IngestResponse {
  task_id: string;
  status: string;
  message?: string;
}

export interface TaskStatus {
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress: number;
  current_step?: string;
}

const headers = {
  'Content-Type': 'application/json',
  'X-API-Key': API_KEY,
};

export const api = {
  async search(params: SearchRequest): Promise<SearchResponse> {
    const response = await fetch(`${API_BASE_URL}/v1/search`, {
      method: 'POST',
      headers,
      body: JSON.stringify(params),
    });
    if (!response.ok) throw new Error('Search failed');
    return response.json();
  },

  async ingest(params: IngestRequest): Promise<IngestResponse> {
    const response = await fetch(`${API_BASE_URL}/v1/ingest`, {
      method: 'POST',
      headers,
      body: JSON.stringify(params),
    });
    if (!response.ok) throw new Error('Ingestion failed');
    return response.json();
  },

  async uploadFile(file: File): Promise<IngestResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/v1/ingest/file`, {
      method: 'POST',
      headers: {
        'X-API-Key': API_KEY, // Note: no Content-Type here, fetch adds it with boundary
      },
      body: formData,
    });
    if (!response.ok) throw new Error('File upload failed');
    return response.json();
  },

  async getTaskStatus(taskId: string): Promise<TaskStatus> {
    const response = await fetch(`${API_BASE_URL}/v1/tasks/${taskId}`, {
      method: 'GET',
      headers,
    });
    if (!response.ok) throw new Error('Task status check failed');
    return response.json();
  },
};
