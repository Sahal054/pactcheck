
import type {
  Health,
  IndexResult,
  IndexStatus,
  ReviewReport,
  UploadedFile,
} from '../types/api';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

async function request<T>(
  url: string,
  init?: RequestInit
): Promise<T> {
  const res = await fetch(`${BASE_URL}/api${url}`, init);

  if (!res.ok) {
    const errBody = await res.json().catch(() => ({}));
    throw new Error(errBody.detail || `Request failed (${res.status})`);
  }

  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<Health>('/health'),

  indexStatus: () =>
    request<IndexStatus>('/playbook/index-status'),

  uploadContract: (file: File) => {
    const form = new FormData();
    form.append('file', file);

    return request<UploadedFile>('/contracts/upload', {
      method: 'POST',
      body: form,
    });
  },

  uploadPlaybook: (file: File) => {
    const form = new FormData();
    form.append('file', file);

    return request<UploadedFile>('/playbook/upload', {
      method: 'POST',
      body: form,
    });
  },


  indexPlaybook: (path: string) => {
    const form = new FormData();
    form.append('path', path);

    return request<IndexResult>('/playbook/index', {
      method: 'POST',
      body: form,
    });
  },


review: (contractPath: string, documentType: string) => {
  const form = new FormData();

  form.append('path', contractPath);
  form.append('document_type', documentType);

  return request<ReviewReport>('/review/analyze', {
    method: 'POST',
    body: form,
  });
},
};
