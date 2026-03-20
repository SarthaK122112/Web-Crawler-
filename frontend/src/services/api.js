/**
 * API service layer for communicating with the FastAPI backend.
 *
 * All endpoints return Axios promises. The baseURL uses the
 * proxy configured in package.json during development.
 */

import axios from 'axios';

const API = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

/**
 * Start a new dark-pattern audit.
 * @param {Object} params - { url, topic, max_pages, threshold }
 * @returns {Promise} - { task_id, status, message }
 */
export const startAudit = (params) =>
  API.post('/start-audit', params).then((r) => r.data);

/**
 * Poll the current status of an audit task.
 * @param {string} taskId
 * @returns {Promise} - { task_id, status, pages_crawled, pages_total, patterns_found }
 */
export const getAuditStatus = (taskId) =>
  API.get(`/audit-status/${taskId}`).then((r) => r.data);

/**
 * Retrieve full results for a completed audit.
 * @param {string} taskId
 * @returns {Promise} - { audit, pages, patterns, screenshots, graph }
 */
export const getResults = (taskId) =>
  API.get(`/results/${taskId}`).then((r) => r.data);

/**
 * Retrieve only the detected dark patterns.
 * @param {string} taskId
 * @returns {Promise} - { task_id, patterns, count }
 */
export const getPatterns = (taskId) =>
  API.get(`/patterns/${taskId}`).then((r) => r.data);

/**
 * Retrieve screenshot metadata for an audit.
 * @param {string} taskId
 * @returns {Promise} - { task_id, screenshots }
 */
export const getScreenshots = (taskId) =>
  API.get(`/screenshots/${taskId}`).then((r) => r.data);

/**
 * Retrieve React Flow-compatible graph data.
 * @param {string} taskId
 * @returns {Promise} - { nodes, edges }
 */
export const getGraphData = (taskId) =>
  API.get(`/graph/${taskId}`).then((r) => r.data);

export default API;
