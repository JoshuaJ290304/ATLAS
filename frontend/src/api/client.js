import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1",
  timeout: 15000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("atlas_access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("atlas_access_token");
      window.dispatchEvent(new CustomEvent("atlas:session-expired"));
    }
    return Promise.reject(error);
  },
);

export default api;
