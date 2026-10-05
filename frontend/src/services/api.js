import axios from 'axios'

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api' })
export const uploadDataset = file => { const body = new FormData(); body.append('file', file); return api.post('/upload', body) }
export const getDataset = id => api.get(`/dataset/${id}`)
export const getSummary = id => api.get(`/summary/${id}`)
export const runChiSquareAnalysis = payload => api.post('/analyze', payload)
export const getFeatureDetails = (id, feature) => api.get(`/feature/${id}/${encodeURIComponent(feature)}`)
export const runMLAnalysis = payload => api.post('/ml-analysis', payload)
export const generateReport = payload => api.post('/generate-report', payload, { responseType: 'blob' })
export const exportSelectedFeatures = payload => api.post('/export', payload, { responseType: 'blob' })
