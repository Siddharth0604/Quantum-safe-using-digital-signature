import axios from 'axios';
export const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000/api', timeout: 120000 });
export async function downloadBlob(url, form, fallback) {
  const response = await api.post(url, form, { responseType: 'blob', headers: { 'Content-Type': 'multipart/form-data' } });
  const disposition = response.headers['content-disposition'] || '';
  const name = disposition.match(/filename="?([^";]+)"?/)?.[1] || fallback;
  const link = document.createElement('a'); link.href = URL.createObjectURL(response.data); link.download = name;
  link.click(); setTimeout(() => URL.revokeObjectURL(link.href), 1000); return name;
}
