import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, BookOpen, Zap, LogOut, Clock, AlertCircle, CheckCircle, XCircle, TrendingUp, Award } from 'lucide-react';
import { motion } from 'framer-motion';
import { dashboardAPI, authenticationAPI, studySessionAPI } from '../services/api';
import { useLanguage } from '../i18n/LanguageContext';
import FeatureSidebar from '../components/FeatureSidebar';

export default function Dashboard() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState(null);
  const [error, setError] = useState(null);
  const [retryingIds, setRetryingIds] = useState(new Set());

  useEffect(() => {
    loadDashboard();
  }, []);

  // Auto-refresh when assessments are being generated
  useEffect(() => {
    const hasGenerating = dashboardData?.weekly_sessions?.some(s => s.test_status?.generating);
    if (!hasGenerating) return;
    const interval = setInterval(loadDashboard, 10000); // refresh every 10s
    return () => clearInterval(interval);
  }, [dashboardData]);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const response = await dashboardAPI.getOverview();
      setDashboardData(response.data);
      setError(null);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = async (sessionId) => {
    try {
      setRetryingIds(prev => new Set([...prev, sessionId]));
      await studySessionAPI.retryGeneration(sessionId);
      // Refresh dashboard after a short delay to see "Generating" state
      setTimeout(loadDashboard, 1000);
    } catch (err) {
      console.error('Failed to retry generation:', err);
      alert('Failed to trigger retry. Please check your connection.');
    } finally {
      setRetryingIds(prev => {
        const next = new Set(prev);
        next.delete(sessionId);
        return next;
      });
    }
  };

  const handleLogout = async () => {
    try {
      await authenticationAPI.signout();
    } catch (err) {
      console.error('Logout error:', err);
    }
    navigate('/signin');
  };

  const formatTime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const getTimeRemaining = (expiresAt) => {
    if (!expiresAt) return t('common.expired');
    const now = new Date();
    const expiry = new Date(expiresAt);
    const diff = expiry - now;

    if (diff <= 0) return t('common.expired');

    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

    return `${hours}h ${minutes}m`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-950 to-slate-950 flex items-center justify-center">
        <div className="text-white text-xl">{t('common.loading')}</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-950 to-slate-950 flex items-center justify-center">
        <div className="text-red-400 text-xl">{error}</div>
      </div>
    );
  }

  const {
    completion_percentage = 0,
    total_sessions = 0,
    completed_tests = 0,
    pending_tests = 0,
    weekly_sessions = [],
    session_limit = {},
    weak_points_count = 0,
    stats = {}
  } = dashboardData || {};

  return (
    <>
      <FeatureSidebar />
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-950 to-slate-950 text-white ml-14">
        {/* Header */}
        <header className="border-b border-white/10 backdrop-blur-sm sticky top-0 z-50 bg-slate-950/50">
          <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Zap className="w-8 h-8 text-pink-500" fill="#E945F5" />
              <span className="text-xl font-bold">{t('common.velocity')}</span>
            </div>
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/adaptive-suggestions')}
                className="flex items-center gap-2 px-4 py-2 bg-purple-500/20 hover:bg-purple-500/30 rounded-lg transition-colors border border-purple-500/30"
              >
                <TrendingUp className="w-5 h-5 text-purple-400" />
                <span className="text-sm font-medium">{t('dashboard.adaptiveSuggestions')}</span>
              </button>
              <button
                onClick={() => navigate('/course-suggestions')}
                className="flex items-center gap-2 px-4 py-2 bg-blue-500/20 hover:bg-blue-500/30 rounded-lg transition-colors border border-blue-500/30"
              >
                <Award className="w-5 h-5 text-blue-400" />
                <span className="text-sm font-medium">{t('dashboard.courseSuggestions')}</span>
              </button>
              <button
                onClick={handleLogout}
                className="p-2 hover:bg-white/5 rounded-lg transition-colors"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          </div>
        </header>

        {/* Completion Bar - Very Top */}
        <div className="bg-slate-900/50 border-b border-white/10">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">{t('dashboard.overallCompletion')}</span>
              <span className="text-2xl font-bold text-pink-500">{completion_percentage.toFixed(1)}%</span>
            </div>
            <div className="w-full h-3 bg-white/10 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${completion_percentage}%` }}
                transition={{ duration: 1, ease: "easeOut" }}
                className="h-full bg-gradient-to-r from-pink-500 to-blue-500 rounded-full"
              />
            </div>
            <div className="flex items-center justify-between mt-2 text-xs text-gray-400">
              <span>{completed_tests} {t('dashboard.testsCompleted')}</span>
              <span>{total_sessions} {t('dashboard.totalSessions')}</span>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-6 py-8">
          {/* Session Limit & Create Button */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold mb-2">{t('dashboard.myStudySessions')}</h1>
              <div className="flex items-center gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${session_limit.can_create ? 'bg-green-500' : 'bg-red-500'}`} />
                  <span className="text-gray-400">
                    {session_limit.sessions_today || 0}/{session_limit.max_sessions || 3} {t('dashboard.sessionsToday')}
                  </span>
                </div>
                {pending_tests > 0 && (
                  <div className="flex items-center gap-2 text-orange-400">
                    <AlertCircle className="w-4 h-4" />
                    <span>{pending_tests} {pending_tests > 1 ? t('dashboard.pendingTests') : t('dashboard.pendingTest')}</span>
                  </div>
                )}
              </div>
            </div>

            {session_limit.can_create ? (
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => navigate('/create-session')}
                className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-pink-500 to-blue-500 rounded-lg font-semibold hover:shadow-lg hover:shadow-pink-500/50 transition-all"
              >
                <Plus className="w-5 h-5" />
                {t('dashboard.createNewSession')}
              </motion.button>
            ) : (
              <div className="text-right">
                <div className="px-6 py-3 bg-red-500/20 border border-red-500/30 rounded-lg">
                  <div className="flex items-center gap-2 text-red-400 mb-1">
                    <XCircle className="w-5 h-5" />
                    <span className="font-semibold">{t('dashboard.cannotCreateSession')}</span>
                  </div>
                  <p className="text-sm text-gray-400">{session_limit.blocked_reason}</p>
                </div>
              </div>
            )}
          </div>

          {/* Pending Tests Section */}
          {pending_tests > 0 && (
            <div className="mb-8">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <AlertCircle className="w-6 h-6 text-orange-400" />
                {t('dashboard.pendingTestsTitle')}
              </h2>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {weekly_sessions
                  .filter(s => s.test_status?.exists && !s.test_status?.completed && !s.test_status?.expired)
                  .map((session) => (
                    <motion.div
                      key={session.id}
                      whileHover={{ y: -4 }}
                      className="p-6 rounded-xl bg-orange-500/10 border border-orange-500/30 hover:border-orange-500/50 transition-all"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="p-2 rounded-lg bg-orange-500/20">
                          <BookOpen className="w-5 h-5 text-orange-400" />
                        </div>
                        <div className="flex items-center gap-1 text-orange-400 text-sm">
                          <Clock className="w-4 h-4" />
                          <span>{getTimeRemaining(session.test_status?.expires_at)}</span>
                        </div>
                      </div>
                      <h3 className="font-bold mb-2">{session.workspace_name}</h3>
                      <p className="text-sm text-gray-400 mb-1">
                        {t('dashboard.sessionCompleted')} {new Date(session.ended_at).toLocaleDateString()}
                      </p>
                      <p className="text-xs text-purple-400 mb-4">
                        Test {session.test_status?.test_number || 1}
                      </p>
                      <button
                        onClick={() => navigate(`/assessment/${session.test_status?.assessment_id}`)}
                        className="w-full py-2 bg-orange-500 hover:bg-orange-600 rounded-lg font-semibold transition-colors"
                      >
                        {t('dashboard.startTest')}
                      </button>
                    </motion.div>
                  ))}
              </div>
            </div>
          )}

          {/* Weekly Sessions Grid */}
          <div className="mb-8">
            <h2 className="text-xl font-bold mb-4">{t('dashboard.thisWeeksSessions')}</h2>
            {weekly_sessions.length === 0 ? (
              <div className="text-center py-12 bg-white/5 rounded-xl border border-white/10">
                <BookOpen className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                <p className="text-gray-400 mb-4">{t('dashboard.noSessionsThisWeek')}</p>
                <button
                  onClick={() => navigate('/create-session')}
                  className="px-6 py-2 bg-gradient-to-r from-pink-500 to-blue-500 rounded-lg font-semibold"
                >
                  {t('dashboard.createFirstSession')}
                </button>
              </div>
            ) : (
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                {weekly_sessions.map((session) => {
                  const testStatus = session.test_status || {};
                  const isCompleted = session.is_completed;
                  const hasTest = testStatus.exists;
                  const testCompleted = testStatus.completed;
                  const testExpired = testStatus.expired;
                  const isGenerating = testStatus.generating;

                  return (
                    <motion.div
                      key={session.id}
                      whileHover={{ y: -4 }}
                      className="p-6 rounded-xl bg-white/5 backdrop-blur-lg border border-white/10 hover:border-pink-500/30 transition-all"
                    >
                      <div className="flex items-start justify-between mb-4">
                        <div className="p-3 rounded-xl bg-gradient-to-br from-pink-500/20 to-blue-500/20">
                          <BookOpen className="w-6 h-6 text-pink-400" />
                        </div>
                        <div className="flex flex-col items-end gap-1">
                          {isCompleted ? (
                            <span className="px-2 py-1 rounded-full bg-green-500/20 text-green-400 text-xs flex items-center gap-1">
                              <CheckCircle className="w-3 h-3" />
                              {t('dashboard.completed')}
                            </span>
                          ) : (
                            <span className="px-2 py-1 rounded-full bg-blue-500/20 text-blue-400 text-xs">
                              {t('dashboard.inProgress')}
                            </span>
                          )}
                          {hasTest && (
                            testCompleted ? (
                              <span className="px-2 py-1 rounded-full bg-green-500/20 text-green-400 text-xs">
                                Test: {testStatus.score?.toFixed(0)}%
                              </span>
                            ) : testExpired ? (
                              <span className="px-2 py-1 rounded-full bg-red-500/20 text-red-400 text-xs">
                                {t('dashboard.testExpired')}
                              </span>
                            ) : (
                              <span className="px-2 py-1 rounded-full bg-orange-500/20 text-orange-400 text-xs">
                                {t('dashboard.testPending')}
                              </span>
                            )
                          )}
                          {isGenerating && (
                            <span className="px-2 py-1 rounded-full bg-yellow-500/20 text-yellow-400 text-xs flex items-center gap-1 animate-pulse">
                              <Clock className="w-3 h-3" />
                              Generating...
                            </span>
                          )}
                        </div>
                      </div>

                      <h3 className="text-lg font-bold mb-2">{session.workspace_name}</h3>
                      <div className="space-y-1 text-sm text-gray-400 mb-4">
                        <div className="flex items-center justify-between">
                          <span>{t('common.type')}:</span>
                          <span className="capitalize">{session.session_type}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span>{t('common.duration')}:</span>
                          <span>{formatTime(session.study_duration_seconds)}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span>{t('common.date')}:</span>
                          <span>{new Date(session.started_at).toLocaleDateString()}</span>
                        </div>
                      </div>

                      {!isCompleted && (
                        <button
                          onClick={() => navigate(`/study-session/${session.id}`)}
                          className="w-full py-2 bg-gradient-to-r from-pink-500 to-blue-500 rounded-lg font-semibold hover:shadow-lg transition-all"
                        >
                          {t('dashboard.continueSession')}
                        </button>
                      )}

                      {isCompleted && isGenerating && (
                        <div className="w-full py-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg text-center">
                          <div className="flex items-center justify-center gap-2 text-yellow-400">
                            <div className="w-4 h-4 border-2 border-yellow-400 border-t-transparent rounded-full animate-spin" />
                            <span className="text-sm font-medium">Questions are being generated...</span>
                          </div>
                          <p className="text-xs text-gray-400 mt-1">Refresh in a moment to take your test</p>
                        </div>
                      )}

                      {isCompleted && testStatus.failed && (
                        <div className="w-full p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
                          <div className="flex items-center gap-2 text-red-400 mb-2">
                            <AlertCircle className="w-4 h-4" />
                            <span className="text-sm font-bold">Generation Failed</span>
                          </div>
                          <p className="text-xs text-gray-400 mb-3 line-clamp-2">
                            {testStatus.error_message || "An error occurred while generating questions."}
                          </p>
                          <button
                            onClick={() => handleRetry(session.id)}
                            disabled={retryingIds.has(session.id)}
                            className="w-full py-1.5 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded flex items-center justify-center gap-2 text-xs font-bold transition-colors disabled:opacity-50"
                          >
                            {retryingIds.has(session.id) ? (
                              <div className="w-3 h-3 border-2 border-red-400 border-t-transparent rounded-full animate-spin" />
                            ) : (
                              <Zap className="w-3 h-3" />
                            )}
                            {retryingIds.has(session.id) ? "Retrying..." : "Try Again"}
                          </button>
                        </div>
                      )}

                      {isCompleted && hasTest && !testCompleted && !testExpired && (
                        <button
                          onClick={() => navigate(`/assessment/${testStatus.assessment_id}`)}
                          className="w-full py-2 bg-orange-500 hover:bg-orange-600 rounded-lg font-semibold transition-colors"
                        >
                          {t('dashboard.takeTest')} {testStatus.test_number === 2 ? '(Adaptive Retry)' : ''}
                        </button>
                      )}

                      {testCompleted && (
                        <button
                          onClick={() => navigate(`/assessment/${testStatus.assessment_id}`)}
                          className="w-full py-2 bg-white/10 hover:bg-white/20 rounded-lg font-semibold transition-colors"
                        >
                          {t('dashboard.viewResults')}
                        </button>
                      )}
                    </motion.div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Quick Stats */}
          <div className="grid md:grid-cols-4 gap-4">
            <div className="p-6 rounded-xl bg-white/5 border border-white/10">
              <div className="text-3xl font-bold text-pink-500 mb-2">
                {formatTime(stats.total_study_time || 0)}
              </div>
              <div className="text-sm text-gray-400">{t('dashboard.totalStudyTime')}</div>
            </div>
            <div className="p-6 rounded-xl bg-white/5 border border-white/10">
              <div className="text-3xl font-bold text-blue-500 mb-2">
                {stats.sessions_this_week || 0}
              </div>
              <div className="text-sm text-gray-400">{t('dashboard.sessionsThisWeek')}</div>
            </div>
            <div className="p-6 rounded-xl bg-white/5 border border-white/10">
              <div className="text-3xl font-bold text-green-500 mb-2">
                {completed_tests}
              </div>
              <div className="text-sm text-gray-400">{t('dashboard.testsCompletedStat')}</div>
            </div>
            <div className="p-6 rounded-xl bg-white/5 border border-white/10">
              <div className="text-3xl font-bold text-orange-500 mb-2">
                {weak_points_count}
              </div>
              <div className="text-sm text-gray-400">{t('dashboard.areasToImprove')}</div>
            </div>
          </div>
        </main>
      </div>
    </>
  );
}
