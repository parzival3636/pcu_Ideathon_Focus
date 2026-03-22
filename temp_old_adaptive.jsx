import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import {
  BookOpen, Youtube, FileText, MessageCircle,
  TrendingUp, AlertCircle, ExternalLink, RefreshCw,
  Award, Clock, BarChart3, Loader, Globe, Search,
  ArrowLeft, Sparkles, Zap, CheckCircle
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const AdaptiveSuggestions = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [weakPointSuggestions, setWeakPointSuggestions] = useState([]);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [stats, setStats] = useState({ articles: 0, playlists: 0, questions: 0 });
  const [usingCuratedData, setUsingCuratedData] = useState(false);

  useEffect(() => {
    // Check if user is authenticated
    const isAuth = localStorage.getItem('isAuthenticated') === 'true';
    const user = localStorage.getItem('user');
    console.log('=== Adaptive Suggestions Page Loaded ===');
    console.log('Is Authenticated:', isAuth);
    console.log('User:', user);
    
    if (!isAuth) {
      console.log('User not authenticated, redirecting to signin');
      navigate('/signin');
      return;
    }
    
    fetchWeakPointSuggestions();
  }, [navigate]);

  const fetchWeakPointSuggestions = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.get('/adaptive-suggestions/weak_point_suggestions/');

      if (response.data.success) {
        const suggestions = response.data.suggestions || [];
        setWeakPointSuggestions(suggestions);
        setUsingCuratedData(response.data.using_curated_data || false);

        // Calculate stats across all suggestions
        let totalArticles = 0, totalPlaylists = 0, totalQuestions = 0;
        suggestions.forEach(item => {
          item.suggestions.forEach(s => {
            if (s.source === 'article') totalArticles++;
            else if (s.source === 'youtube') totalPlaylists++;
            else if (s.source === 'stackoverflow') totalQuestions++;
          });
        });
        setStats({ articles: totalArticles, playlists: totalPlaylists, questions: totalQuestions });

        if (response.data.fallback_used) {
          console.log('Using study session topics as fallback');
        }
      } else {
        setError('Failed to fetch suggestions');
      }
    } catch (error) {
      console.error('Error fetching suggestions:', error);
      setError(error.response?.data?.detail || 'Failed to load suggestions. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async (weakPointId) => {
    if (!weakPointId) {
      fetchWeakPointSuggestions();
      return;
    }

    try {
      setRefreshing(true);
      await api.post('/adaptive-suggestions/refresh_suggestions/', {
        weak_point_id: weakPointId
      });
      await fetchWeakPointSuggestions();
    } catch (error) {
      console.error('Error refreshing suggestions:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const markAsViewed = async (suggestionId) => {
    if (!suggestionId) return;

    try {
      await api.post('/adaptive-suggestions/mark_suggestion_viewed/', {
        suggestion_id: suggestionId
      });
    } catch (error) {
      console.error('Error marking as viewed:', error);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    if (suggestion.id) {
      markAsViewed(suggestion.id);
    }
    window.open(suggestion.url, '_blank', 'noopener,noreferrer');
  };

  const getSourceIcon = (source) => {
    switch (source) {
      case 'youtube':
        return <Youtube className="w-5 h-5 text-red-400" />;
      case 'article':
        return <FileText className="w-5 h-5 text-blue-400" />;
      case 'stackoverflow':
        return <MessageCircle className="w-5 h-5 text-orange-400" />;
      default:
        return <BookOpen className="w-5 h-5 text-purple-400" />;
    }
  };

  const getSourceColor = (source) => {
    switch (source) {
      case 'youtube':
        return { bg: 'bg-red-500/10', border: 'border-red-500/30', hover: 'hover:border-red-500/60', text: 'text-red-400', badge: 'bg-red-500/20 text-red-300' };
      case 'article':
        return { bg: 'bg-blue-500/10', border: 'border-blue-500/30', hover: 'hover:border-blue-500/60', text: 'text-blue-400', badge: 'bg-blue-500/20 text-blue-300' };
      case 'stackoverflow':
        return { bg: 'bg-orange-500/10', border: 'border-orange-500/30', hover: 'hover:border-orange-500/60', text: 'text-orange-400', badge: 'bg-orange-500/20 text-orange-300' };
      default:
        return { bg: 'bg-purple-500/10', border: 'border-purple-500/30', hover: 'hover:border-purple-500/60', text: 'text-purple-400', badge: 'bg-purple-500/20 text-purple-300' };
    }
  };

  const getAccuracyColor = (accuracy) => {
    if (accuracy >= 70) return 'text-green-400';
    if (accuracy >= 50) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getAccuracyBg = (accuracy) => {
    if (accuracy >= 70) return 'bg-green-500/20 border-green-500/30';
    if (accuracy >= 50) return 'bg-yellow-500/20 border-yellow-500/30';
    return 'bg-red-500/20 border-red-500/30';
  };

  // Group suggestions by source type
  const groupBySource = (suggestions) => {
    const grouped = { youtube: [], article: [], stackoverflow: [] };
    suggestions.forEach(s => {
      if (grouped[s.source]) {
        grouped[s.source].push(s);
      }
    });
    return grouped;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-950 to-slate-950 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center"
        >
          <div className="relative">
            <div className="w-20 h-20 rounded-full border-4 border-purple-500/30 border-t-purple-500 animate-spin mx-auto mb-6" />
            <Sparkles className="w-8 h-8 text-purple-400 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
          </div>
          <div className="text-white text-xl font-semibold mb-2">Loading Suggestions</div>
          <div className="text-white/50 text-sm">Analyzing your learning data...</div>
        </motion.div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-950 to-slate-950 flex items-center justify-center p-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-white/5 backdrop-blur-xl rounded-2xl p-12 text-center max-w-md border border-white/10"
        >
          <AlertCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h3 className="text-2xl font-bold text-white mb-2">Something Went Wrong</h3>
          <p className="text-white/60 mb-6">{error}</p>
          <div className="flex gap-4 justify-center">
            <button
              onClick={() => fetchWeakPointSuggestions()}
              className="bg-gradient-to-r from-purple-500 to-pink-500 text-white px-6 py-3 rounded-xl hover:shadow-lg hover:shadow-purple-500/25 transition-all font-semibold"
            >
              Try Again
            </button>
            <button
              onClick={() => navigate('/dashboard')}
              className="bg-white/10 text-white px-6 py-3 rounded-xl hover:bg-white/20 transition-all font-semibold"
            >
              Dashboard
            </button>
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-950 to-slate-950 text-white">
      {/* Header */}
      <header className="border-b border-white/10 backdrop-blur-sm sticky top-0 z-50 bg-slate-950/80">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/dashboard')}
                className="p-2 hover:bg-white/5 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div className="flex items-center gap-3">
                <div className="bg-gradient-to-r from-purple-500 to-pink-500 p-2.5 rounded-xl">
                  <TrendingUp className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold">Adaptive Suggestions</h1>
                  <p className="text-white/50 text-sm">Personalized content for your learning journey</p>
                </div>
              </div>
            </div>

            <button
              onClick={() => handleRefresh(null)}
              disabled={refreshing}
              className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 rounded-lg transition-all disabled:opacity-50 border border-white/10"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
              <span className="text-sm font-medium">Refresh</span>
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats Cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8"
        >
          <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 border border-white/10">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 rounded-lg bg-purple-500/20">
                <Sparkles className="w-4 h-4 text-purple-400" />
              </div>
              <span className="text-2xl font-bold text-purple-400">{weakPointSuggestions.length}</span>
            </div>
            <p className="text-xs text-white/50">Topics Analyzed</p>
          </div>
          <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 border border-white/10">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 rounded-lg bg-red-500/20">
                <Youtube className="w-4 h-4 text-red-400" />
              </div>
              <span className="text-2xl font-bold text-red-400">{stats.playlists}</span>
            </div>
            <p className="text-xs text-white/50">Video Resources</p>
          </div>
          <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 border border-white/10">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 rounded-lg bg-blue-500/20">
                <FileText className="w-4 h-4 text-blue-400" />
              </div>
              <span className="text-2xl font-bold text-blue-400">{stats.articles}</span>
            </div>
            <p className="text-xs text-white/50">Articles & Tutorials</p>
          </div>
          <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 border border-white/10">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 rounded-lg bg-orange-500/20">
                <MessageCircle className="w-4 h-4 text-orange-400" />
              </div>
              <span className="text-2xl font-bold text-orange-400">{stats.questions}</span>
            </div>
            <p className="text-xs text-white/50">Q&A Resources</p>
          </div>
        </motion.div>

        {/* Content */}
        {weakPointSuggestions.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white/5 backdrop-blur-lg rounded-2xl p-12 text-center border border-white/10"
          >
            <Search className="w-16 h-16 text-white/20 mx-auto mb-4" />
            <h3 className="text-2xl font-bold text-white mb-2">No Suggestions Yet</h3>
            <p className="text-white/50 mb-6 max-w-md mx-auto">
              Complete some study sessions or assessments to get personalized content suggestions based on your learning patterns.
            </p>
            <button
              onClick={() => navigate('/dashboard')}
              className="bg-gradient-to-r from-purple-500 to-pink-500 text-white px-6 py-3 rounded-xl hover:shadow-lg hover:shadow-purple-500/25 transition-all font-semibold"
            >
              Start Learning
            </button>
          </motion.div>
        ) : (
          <div className="space-y-8">
            <AnimatePresence>
              {weakPointSuggestions.map((item, index) => {
                const grouped = groupBySource(item.suggestions);

                return (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="bg-white/5 backdrop-blur-lg rounded-2xl border border-white/10 overflow-hidden"
                  >
                    {/* Topic Header */}
                    <div className="p-6 border-b border-white/10 bg-gradient-to-r from-white/5 to-transparent">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-3">
                            {item.weak_point.total_attempts > 0 && item.weak_point.accuracy < 70 ? (
                              <div className="p-2 rounded-lg bg-red-500/20">
                                <AlertCircle className="w-5 h-5 text-red-400" />
                              </div>
                            ) : (
                              <div className="p-2 rounded-lg bg-purple-500/20">
                                <Zap className="w-5 h-5 text-purple-400" />
                              </div>
                            )}
                            <h2 className="text-xl font-bold text-white">
                              {item.weak_point.topic}
                            </h2>
                          </div>

                          {item.weak_point.subtopic && (
                            <p className="text-white/50 text-sm ml-12 mb-3">{item.weak_point.subtopic}</p>
                          )}

                          {/* Stats badges */}
                          <div className="flex items-center gap-3 ml-12 flex-wrap">
                            {item.weak_point.total_attempts > 0 && (
                              <>
                                <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border ${getAccuracyBg(item.weak_point.accuracy)}`}>
                                  <BarChart3 className="w-3 h-3" />
                                  <span className={getAccuracyColor(item.weak_point.accuracy)}>
                                    {item.weak_point.accuracy.toFixed(1)}% Accuracy
                                  </span>
                                </div>
                                <div className="text-white/40 text-xs">
                                  {item.weak_point.incorrect_count} incorrect / {item.weak_point.total_attempts} attempts
                                </div>
                              </>
                            )}
                            {item.weak_point.total_attempts === 0 && (
                              <div className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-purple-500/20 border border-purple-500/30 text-purple-300">
                                <BookOpen className="w-3 h-3" />
                                Study topic
                              </div>
                            )}
                            <div className="text-white/30 text-xs">
                              {item.suggestions.length} resources found
                            </div>
                          </div>
                        </div>

                        {item.weak_point.id && (
                          <button
                            onClick={() => handleRefresh(item.weak_point.id)}
                            disabled={refreshing}
                            className="p-2 bg-white/5 hover:bg-white/10 rounded-lg transition-all disabled:opacity-50 border border-white/10"
                            title="Refresh suggestions"
                          >
                            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Suggestions Content */}
                    {item.suggestions.length === 0 ? (
                      <div className="text-center py-10 text-white/40">
                        <Globe className="w-10 h-10 mx-auto mb-3 opacity-50" />
                        <p className="font-medium">No suggestions available yet</p>
                        {item.weak_point.id && (
                          <button
                            onClick={() => handleRefresh(item.weak_point.id)}
                            className="mt-3 text-purple-400 hover:text-purple-300 text-sm font-medium"
                          >
                            Generate Suggestions
                          </button>
                        )}
                      </div>
                    ) : (
                      <div className="p-6 space-y-6">
                        {/* YouTube Section */}
                        {grouped.youtube.length > 0 && (
                          <div>
                            <div className="flex items-center gap-2 mb-3">
                              <Youtube className="w-4 h-4 text-red-400" />
                              <h3 className="text-sm font-semibold text-red-400 uppercase tracking-wider">
                                Video Resources
                              </h3>
                              <span className="text-xs text-white/30 ml-auto">{grouped.youtube.length} found</span>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                              {grouped.youtube.map((suggestion, idx) => (
                                <motion.div
                                  key={idx}
                                  whileHover={{ y: -2, scale: 1.01 }}
                                  onClick={() => handleSuggestionClick(suggestion)}
                                  className={`bg-red-500/5 hover:bg-red-500/10 rounded-xl p-4 cursor-pointer transition-all border border-red-500/20 hover:border-red-500/40 group ${suggestion.viewed ? 'opacity-60' : ''
                                    }`}
                                >
                                  <div className="flex items-start gap-3">
                                    <div className="p-2 rounded-lg bg-red-500/20 flex-shrink-0 mt-0.5">
                                      <Youtube className="w-4 h-4 text-red-400" />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                      <h4 className="text-white font-medium text-sm line-clamp-2 mb-1 group-hover:text-red-300 transition-colors">
                                        {suggestion.title}
                                      </h4>
                                      <p className="text-white/40 text-xs">{suggestion.description}</p>
                                    </div>
                                    <ExternalLink className="w-4 h-4 text-white/20 group-hover:text-red-400 flex-shrink-0 transition-colors" />
                                  </div>
                                  {suggestion.viewed && (
                                    <div className="flex items-center gap-1 mt-2 ml-11">
                                      <CheckCircle className="w-3 h-3 text-green-400" />
                                      <span className="text-xs text-green-400">Viewed</span>
                                    </div>
                                  )}
                                </motion.div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Articles Section */}
                        {grouped.article.length > 0 && (
                          <div>
                            <div className="flex items-center gap-2 mb-3">
                              <FileText className="w-4 h-4 text-blue-400" />
                              <h3 className="text-sm font-semibold text-blue-400 uppercase tracking-wider">
                                Articles & Tutorials
                              </h3>
                              <span className="text-xs text-white/30 ml-auto">{grouped.article.length} found</span>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                              {grouped.article.map((suggestion, idx) => (
                                <motion.div
                                  key={idx}
                                  whileHover={{ y: -2, scale: 1.01 }}
                                  onClick={() => handleSuggestionClick(suggestion)}
                                  className={`bg-blue-500/5 hover:bg-blue-500/10 rounded-xl p-4 cursor-pointer transition-all border border-blue-500/20 hover:border-blue-500/40 group ${suggestion.viewed ? 'opacity-60' : ''
                                    }`}
                                >
                                  <div className="flex items-start gap-3">
                                    <div className="p-2 rounded-lg bg-blue-500/20 flex-shrink-0 mt-0.5">
                                      <FileText className="w-4 h-4 text-blue-400" />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                      <h4 className="text-white font-medium text-sm line-clamp-2 mb-1 group-hover:text-blue-300 transition-colors">
                                        {suggestion.title}
                                      </h4>
                                      <p className="text-white/40 text-xs">{suggestion.description}</p>
                                    </div>
                                    <ExternalLink className="w-4 h-4 text-white/20 group-hover:text-blue-400 flex-shrink-0 transition-colors" />
                                  </div>
                                  {suggestion.viewed && (
                                    <div className="flex items-center gap-1 mt-2 ml-11">
                                      <CheckCircle className="w-3 h-3 text-green-400" />
                                      <span className="text-xs text-green-400">Viewed</span>
                                    </div>
                                  )}
                                </motion.div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Stack Overflow Section */}
                        {grouped.stackoverflow.length > 0 && (
                          <div>
                            <div className="flex items-center gap-2 mb-3">
                              <MessageCircle className="w-4 h-4 text-orange-400" />
                              <h3 className="text-sm font-semibold text-orange-400 uppercase tracking-wider">
                                Community Q&A
                              </h3>
                              <span className="text-xs text-white/30 ml-auto">{grouped.stackoverflow.length} found</span>
                            </div>
                            <div className="space-y-2">
                              {grouped.stackoverflow.map((suggestion, idx) => (
                                <motion.div
                                  key={idx}
                                  whileHover={{ x: 4 }}
                                  onClick={() => handleSuggestionClick(suggestion)}
                                  className={`bg-orange-500/5 hover:bg-orange-500/10 rounded-xl p-4 cursor-pointer transition-all border border-orange-500/20 hover:border-orange-500/40 group flex items-center gap-4 ${suggestion.viewed ? 'opacity-60' : ''
                                    }`}
                                >
                                  <div className="p-2 rounded-lg bg-orange-500/20 flex-shrink-0">
                                    <MessageCircle className="w-4 h-4 text-orange-400" />
                                  </div>
                                  <div className="flex-1 min-w-0">
                                    <h4 className="text-white font-medium text-sm line-clamp-1 group-hover:text-orange-300 transition-colors">
                                      {suggestion.title}
                                    </h4>
                                  </div>
                                  {suggestion.description && (
                                    <span className="text-xs px-2 py-1 rounded-full bg-orange-500/20 text-orange-300 font-medium flex-shrink-0">
                                      {suggestion.description}
                                    </span>
                                  )}
                                  {suggestion.viewed && (
                                    <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
                                  )}
                                  <ExternalLink className="w-4 h-4 text-white/20 group-hover:text-orange-400 flex-shrink-0 transition-colors" />
                                </motion.div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
        )}
      </main>
    </div>
  );
};

export default AdaptiveSuggestions;
