/**
 * API Service Layer for Adaptive Learning Backend
 */
import axios from 'axios';

// Dynamically determine backend host (ensures cookies work for both localhost and 127.0.0.1)
const baseHost = window.location.hostname || '127.0.0.1';
const baseURL = `http://${baseHost}:8000`;

// Create axios instance with base configuration
const api = axios.create({
  baseURL: `${baseURL}/api/adaptive`,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Create separate instance for auth endpoints
const authAPI = axios.create({
  baseURL: baseURL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth tokens if needed
api.interceptors.request.use(
  (config) => {
    // Add CSRF token if available
    const csrfToken = getCookie('csrftoken');
    if (csrfToken) {
      config.headers['X-CSRFToken'] = csrfToken;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login if unauthorized
      window.location.href = '/signin';
    }
    return Promise.reject(error);
  }
);

// Helper function to get CSRF token from cookies
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + '=') {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// ============ AUTHENTICATION API ============
export const authenticationAPI = {
  // Sign up new user
  signup: async (userData) => {
    try {
      // Derive a valid Django username from the email:
      // Replace any characters that aren't alphanumeric, @/./+/-/_ with underscore
      const rawUsername = userData.email.split('@')[0]
        .replace(/[^a-zA-Z0-9_]/g, '_')
        .substring(0, 150);

      const response = await authAPI.post('/accounts/api/register/', {
        username: rawUsername,
        email: userData.email,
        password: userData.password,
        first_name: userData.name.split(' ')[0] || '',
        last_name: userData.name.split(' ').slice(1).join(' ') || '',
      });
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // Sign in user
  signin: async (credentials) => {
    try {
      // Derive username same way as registration
      const username = credentials.email.split('@')[0]
        .replace(/[^a-zA-Z0-9_]/g, '_')
        .substring(0, 150);

      const response = await authAPI.post('/accounts/api/login/', {
        username,
        password: credentials.password,
      });

      // Store user info in localStorage
      if (response.data.user) {
        localStorage.setItem('user', JSON.stringify(response.data.user));
        localStorage.setItem('isAuthenticated', 'true');
      }

      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // Sign out user
  signout: async () => {
    try {
      await authAPI.post('/accounts/api/logout/');
      localStorage.removeItem('user');
      localStorage.removeItem('isAuthenticated');
    } catch (error) {
      throw error;
    }
  },

  // Get current user
  getCurrentUser: () => {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  },

  // Check if user is authenticated
  isAuthenticated: () => {
    return localStorage.getItem('isAuthenticated') === 'true';
  },
};

// ============ TOPICS API ============
export const topicsAPI = {
  // Get all topics for current user
  list: () => api.get('/topics/'),

  // Create new topic
  create: (data) => api.post('/topics/', data),

  // Get single topic
  get: (id) => api.get(`/topics/${id}/`),

  // Update topic
  update: (id, data) => api.patch(`/topics/${id}/`, data),

  // Delete topic
  delete: (id) => api.delete(`/topics/${id}/`),

  // Get topic progress
  getProgress: (id) => api.get(`/topics/${id}/progress/`),

  // Get concept mastery for topic
  getConcepts: (id) => api.get(`/topics/${id}/concepts/`),
};

// ============ CONTENT API ============
export const contentAPI = {
  // Get all content
  list: () => api.get('/content/'),

  // Upload new content
  upload: (formData) => {
    // Don't set Content-Type manually — let axios auto-detect FormData
    // and set multipart/form-data with the correct boundary parameter
    return api.post('/content/upload/', formData, {
      headers: {
        'Content-Type': undefined,
      },
    });
  },

  // Get single content
  get: (id) => api.get(`/content/${id}/`),

  // Generate assessment for content
  generateAssessment: (id) => api.post(`/content/${id}/generate_assessment/`),

  // Delete content
  delete: (id) => api.delete(`/content/${id}/`),

  // Generate Gemini MCQs for content
  generateGeminiMCQs: (id, userState = 4) => {
    return api.post(`/content/${id}/generate_gemini_mcqs/`, {
      user_state: userState,
    });
  },
};

// ============ ASSESSMENT API ============
export const assessmentAPI = {
  // Get all assessments
  list: () => api.get('/assessments/'),

  // Get single assessment
  get: (id) => api.get(`/assessments/${id}/`),

  // Get questions for assessment
  getQuestions: (id) => api.get(`/assessments/${id}/questions/`),

  // Submit answer to a question
  submitAnswer: (assessmentId, data) => {
    return api.post(`/assessments/${assessmentId}/submit_answer/`, data);
  },

  // Complete assessment and get results
  complete: (id) => api.post(`/assessments/${id}/complete/`),
};

// ============ MONITORING API ============
export const monitoringAPI = {
  // Start monitoring session
  startSession: (contentId) => {
    return api.post('/monitoring/start_session/', { content_id: contentId });
  },

  // Track engagement event
  trackEvent: (sessionId, eventType, data = {}) => {
    return api.post(`/monitoring/${sessionId}/track_event/`, {
      event_type: eventType,
      data: data,
    });
  },

  // End monitoring session
  endSession: (sessionId) => {
    return api.post(`/monitoring/${sessionId}/end_session/`);
  },
};

// ============ PROGRESS API ============
export const progressAPI = {
  // Get all progress
  list: () => api.get('/progress/'),

  // Get progress overview
  getOverview: () => api.get('/progress/overview/'),

  // Get single progress
  get: (id) => api.get(`/progress/${id}/`),
};

// ============ STUDY SESSION API ============
export const studySessionAPI = {
  // Create new study session
  create: (data) => api.post('/study-sessions/', data),

  // Get a session by ID
  get: (id) => api.get(`/study-sessions/${id}/`),

  // Get session status
  getStatus: (id) => api.get(`/study-sessions/${id}/status/`),

  // Start break
  startBreak: (id) => api.post(`/study-sessions/${id}/start_break/`),

  // End break
  endBreak: (id) => api.post(`/study-sessions/${id}/end_break/`),

  // Complete session
  complete: (id) => api.post(`/study-sessions/${id}/complete/`),

  // Update camera status
  updateCamera: (id, enabled) => {
    return api.post(`/study-sessions/${id}/update_camera/`, { enabled });
  },

  // Update session content (when user adds YouTube video)
  updateContent: (id, contentId) => {
    return api.post(`/study-sessions/${id}/update_content/`, { content_id: contentId });
  },

  // Get session metrics
  getMetrics: (id) => api.get(`/study-sessions/${id}/metrics/`),

  // Get violations summary
  getViolations: (id) => api.get(`/study-sessions/${id}/violations/`),

  // Retry test generation
  retryGeneration: (id) => api.post(`/study-sessions/${id}/retry_generation/`),
};

// ============ SESSION MONITORING API ============
export const sessionMonitoringAPI = {
  // Record monitoring event
  recordEvent: (sessionId, eventType, eventData = {}) => {
    return api.post('/session-monitoring/', {
      session_id: sessionId,
      event_type: eventType,
      event_data: eventData,
    });
  },

  // Update real-time metrics
  updateMetrics: (sessionId) => {
    return api.post('/session-monitoring/update_metrics/', {
      session_id: sessionId,
    });
  },
};

// ============ PROCTORING API ============
export const proctoringAPI = {
  // Record proctoring event
  recordEvent: (sessionId, eventType, data = {}) => {
    return api.post('/proctoring/', {
      session_id: sessionId,
      event_type: eventType,
      ...data,
    });
  },

  // Record tab switch
  recordTabSwitch: (sessionId) => {
    return proctoringAPI.recordEvent(sessionId, 'tab_switch');
  },

  // Record copy attempt
  recordCopyAttempt: (sessionId) => {
    return proctoringAPI.recordEvent(sessionId, 'copy_attempt');
  },

  // Record paste attempt
  recordPasteAttempt: (sessionId) => {
    return proctoringAPI.recordEvent(sessionId, 'paste_attempt');
  },

  // Record focus lost
  recordFocusLost: (sessionId) => {
    return proctoringAPI.recordEvent(sessionId, 'focus_lost');
  },

  // Record focus gained
  recordFocusGained: (sessionId) => {
    return proctoringAPI.recordEvent(sessionId, 'focus_gained');
  },

  // Record screenshot attempt
  recordScreenshot: (sessionId, source = 'content') => {
    return proctoringAPI.recordEvent(sessionId, 'screenshot_attempt', { source });
  },
};

// ============ TEST API ============
export const testAPI = {
  // Get all tests
  list: () => api.get('/tests/'),

  // Get single test with questions
  get: (id) => api.get(`/tests/${id}/`),

  // Generate test from session
  generate: (sessionId, difficulty = 1) => {
    return api.post('/tests/generate/', {
      session_id: sessionId,
      difficulty: difficulty,
    });
  },

  // Start test
  start: (id) => api.post(`/tests/${id}/start/`),

  // Submit answer
  submitAnswer: (id, data) => {
    return api.post(`/tests/${id}/submit_answer/`, data);
  },

  // Complete test
  complete: (id) => api.post(`/tests/${id}/complete/`),
};

// ============ WHITEBOARD API ============
export const whiteboardAPI = {
  // Save whiteboard snapshot
  save: (sessionId, imageData, notes = '') => {
    return api.post('/whiteboard/', {
      session_id: sessionId,
      image_data: imageData,
      notes: notes,
    });
  },

  // Download whiteboard
  download: (sessionId) => {
    return api.get('/whiteboard/download/', {
      params: { session_id: sessionId },
    });
  },
};

// ============ CHAT API ============
export const chatAPI = {
  // Send chat query
  sendQuery: (sessionId, query, context = null) => {
    return api.post('/chat/', {
      session_id: sessionId,
      query: query,
      context: context,
    });
  },

  // Get chat history
  getHistory: (sessionId) => {
    return api.get('/chat/history/', {
      params: { session_id: sessionId },
    });
  },
};

// ============ HELPER FUNCTIONS ============

/**
 * Upload content with proper formatting
 */
export async function uploadContent(topicId, contentData) {
  const formData = new FormData();
  formData.append('topic', topicId);
  formData.append('title', contentData.title);
  formData.append('content_type', contentData.type);

  if (contentData.type === 'youtube') {
    formData.append('url', contentData.url);
  } else {
    formData.append('file', contentData.file);
  }

  return contentAPI.upload(formData);
}

/**
 * Create topic and return the created topic
 */
export async function createTopic(name, description = '') {
  const response = await topicsAPI.create({ name, description });
  return response.data;
}

/**
 * Get full assessment with questions
 */
export async function getAssessmentWithQuestions(assessmentId) {
  const [assessment, questions] = await Promise.all([
    assessmentAPI.get(assessmentId),
    assessmentAPI.getQuestions(assessmentId),
  ]);

  return {
    ...assessment.data,
    questions: questions.data,
  };
}

/**
 * Submit all answers and complete assessment
 */
export async function submitAssessment(assessmentId, answers) {
  // Submit each answer
  for (const answer of answers) {
    await assessmentAPI.submitAnswer(assessmentId, answer);
  }

  // Complete assessment and get results
  const results = await assessmentAPI.complete(assessmentId);
  return results.data;
}

/**
 * Create and start a study session
 */
export async function createStudySession(contentId, sessionType = 'recommended', workspaceName = 'My Study Session') {
  const response = await studySessionAPI.create({
    content_id: contentId,
    session_type: sessionType,
    workspace_name: workspaceName,
  });
  return response.data;
}

/**
 * Complete study session and generate test
 */
export async function completeStudySession(sessionId, difficulty = 1) {
  const response = await studySessionAPI.complete(sessionId);

  if (response.data.test) {
    return response.data.test;
  }

  // Generate test if not automatically created
  const testResponse = await testAPI.generate(sessionId, difficulty);
  return testResponse.data;
}

// ============ DASHBOARD API ============
export const dashboardAPI = {
  // Get dashboard overview
  getOverview: () => api.get('/dashboard/overview/'),

  // Get weekly sessions
  getWeeklySessions: () => api.get('/dashboard/weekly_sessions/'),

  // Get completion stats
  getCompletionStats: () => api.get('/dashboard/completion_stats/'),
};

// ============ WEAK POINTS API ============
export const weakPointsAPI = {
  // Get all weak points
  list: () => api.get('/weak-points/'),

  // Get recommendations for all weak points
  getRecommendations: () => api.get('/weak-points/recommendations/'),

  // Generate recommendations for specific weak point
  generateRecommendations: (weakPointId) => {
    return api.post(`/weak-points/${weakPointId}/generate_recommendations/`);
  },

  // Mark recommendation as viewed
  markViewed: (weakPointId, recommendationId) => {
    return api.post(`/weak-points/${weakPointId}/mark_viewed/`, {
      recommendation_id: recommendationId,
    });
  },
};

// ============ BROWSER EXTENSION API ============
export const extensionAPI = {
  // Send heartbeat
  heartbeat: (sessionId, data) => {
    return api.post('/extension/heartbeat/', {
      session_id: sessionId,
      ...data,
    });
  },

  // Log violation
  logViolation: (sessionId, eventType, url = '') => {
    return api.post('/extension/violation/', {
      session_id: sessionId,
      event_type: eventType,
      url: url,
    });
  },

  // Get extension status
  getStatus: (sessionId) => {
    return api.get('/extension/status/', {
      params: { session_id: sessionId },
    });
  },
};

// ============ ADAPTIVE SUGGESTIONS API ============
export const adaptiveSuggestionsAPI = {
  // Get weak point suggestions (Adaptive Suggestions page)
  getWeakPointSuggestions: () => api.get('/adaptive-suggestions/weak_point_suggestions/'),

  // Get recent topic suggestions (Course Suggestions page)
  getRecentTopicSuggestions: () => api.get('/adaptive-suggestions/recent_topic_suggestions/'),

  // Get Coursera certificate recommendations
  getCourseraCertificates: () => api.get('/adaptive-suggestions/coursera_certificates/'),

  // Refresh suggestions for a specific weak point
  refreshSuggestions: (weakPointId) => {
    return api.post('/adaptive-suggestions/refresh_suggestions/', {
      weak_point_id: weakPointId,
    });
  },

  // Mark a suggestion as viewed
  markViewed: (suggestionId) => {
    return api.post('/adaptive-suggestions/mark_suggestion_viewed/', {
      suggestion_id: suggestionId,
    });
  },

  // Get scraper status for user's topics
  getScraperStatus: () => api.get('/adaptive-suggestions/scraper_status/'),
};

export default api;
