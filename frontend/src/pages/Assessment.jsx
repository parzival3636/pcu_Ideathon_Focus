import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { CheckCircle, XCircle, Zap, Loader, AlertTriangle, Camera, CameraOff, Shield } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../services/api';

export default function Assessment() {
  const navigate = useNavigate();
  const { assessmentId } = useParams();

  // Test state
  const [loading, setLoading] = useState(true);
  const [assessment, setAssessment] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState({}); // Stores index for MCQ, string for open-ended
  const [showResults, setShowResults] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // Proctoring state
  const [tabSwitchCount, setTabSwitchCount] = useState(0);
  const [warningMessage, setWarningMessage] = useState(null);
  const [testTerminated, setTestTerminated] = useState(false);
  const [cameraStream, setCameraStream] = useState(null);
  const [cameraError, setCameraError] = useState(false);
  const videoRef = useRef(null);
  const warningTimerRef = useRef(null);
  const startTimeRef = useRef(Date.now());
  const questionTimesRef = useRef({});

  // ─── Load Assessment ──────────────────────────────────────────────────
  useEffect(() => {
    if (assessmentId) loadAssessment();
  }, [assessmentId]);

  const loadAssessment = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get(`/assessments/${assessmentId}/`);
      if (!response.data) throw new Error('No data received');

      setAssessment(response.data);
      const q = response.data.questions || [];
      setQuestions(q);
      if (q.length === 0) setError('No questions found in this assessment.');
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load assessment.');
    } finally {
      setLoading(false);
    }
  };

  // ─── Camera / Webcam ─────────────────────────────────────────────────
  useEffect(() => {
    startCamera();
    return () => stopCamera();
  }, []);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 320, height: 240, facingMode: 'user' },
        audio: false,
      });
      setCameraStream(stream);
      if (videoRef.current) videoRef.current.srcObject = stream;
    } catch (e) {
      console.warn('[Proctor] Camera access denied:', e);
      setCameraError(true);
    }
  };

  const stopCamera = () => {
    if (cameraStream) cameraStream.getTracks().forEach(t => t.stop());
  };

  useEffect(() => {
    if (videoRef.current && cameraStream) {
      videoRef.current.srcObject = cameraStream;
    }
  }, [cameraStream]);

  // ─── Tab Switch Detection (3 max) ─────────────────────────────────────
  const handleVisibilityChange = useCallback(() => {
    if (document.hidden && !showResults && !testTerminated && questions.length > 0) {
      setTabSwitchCount(prev => {
        const newCount = prev + 1;
        if (newCount >= 3) {
          setWarningMessage('⛔ Test terminated! You exceeded the tab switch limit.');
          setTestTerminated(true);
          // Auto-submit after a brief delay
          setTimeout(() => autoSubmitTest(), 2000);
        } else {
          const remaining = 3 - newCount;
          setWarningMessage(
            `⚠️ Warning ${newCount}/3: Tab switch detected! ${remaining} more and your test will be auto-submitted.`
          );
          // Clear warning after 5s
          if (warningTimerRef.current) clearTimeout(warningTimerRef.current);
          warningTimerRef.current = setTimeout(() => setWarningMessage(null), 5000);
        }
        return newCount;
      });
    }
  }, [showResults, testTerminated, questions.length]);

  useEffect(() => {
    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [handleVisibilityChange]);

  // ─── Copy / Screenshot Prevention ─────────────────────────────────────
  useEffect(() => {
    const preventCopy = (e) => { e.preventDefault(); return false; };
    const preventKey = (e) => {
      // Block: Ctrl+C, Ctrl+V, Ctrl+A, Ctrl+P, PrintScreen, Ctrl+Shift+I
      if (
        (e.ctrlKey && ['c', 'v', 'a', 'p', 'u', 's'].includes(e.key.toLowerCase())) ||
        e.key === 'PrintScreen' ||
        (e.ctrlKey && e.shiftKey && ['i', 'j', 'c'].includes(e.key.toLowerCase())) ||
        e.key === 'F12'
      ) {
        e.preventDefault();
        e.stopPropagation();
        return false;
      }
    };
    const preventContext = (e) => { e.preventDefault(); return false; };

    document.addEventListener('copy', preventCopy, true);
    document.addEventListener('cut', preventCopy, true);
    document.addEventListener('paste', preventCopy, true);
    document.addEventListener('keydown', preventKey, true);
    document.addEventListener('contextmenu', preventContext, true);

    // CSS-based selection prevention
    document.body.style.userSelect = 'none';
    document.body.style.webkitUserSelect = 'none';

    return () => {
      document.removeEventListener('copy', preventCopy, true);
      document.removeEventListener('cut', preventCopy, true);
      document.removeEventListener('paste', preventCopy, true);
      document.removeEventListener('keydown', preventKey, true);
      document.removeEventListener('contextmenu', preventContext, true);
      document.body.style.userSelect = '';
      document.body.style.webkitUserSelect = '';
    };
  }, []);

  // ─── Auto-submit on termination ───────────────────────────────────────
  const autoSubmitTest = async () => {
    try {
      setSubmitting(true);
      for (let i = 0; i < questions.length; i++) {
        const q = questions[i];
        const sel = selectedAnswers[i];
        if (sel !== undefined) {
          const payload = {
            question_id: q.id,
            time_taken_seconds: questionTimesRef.current[i] || 60,
          };
          
          if (q.question_type === 'mcq') {
            payload.selected_answer_index = sel;
          } else {
            payload.user_answer = sel;
          }

          await api.post(`/assessments/${assessmentId}/submit_answer/`, payload);
        }
      }
      await api.post(`/assessments/${assessmentId}/complete/`);
      setShowResults(true);
    } catch (err) {
      console.error('Auto-submit failed:', err);
    } finally {
      setSubmitting(false);
    }
  };

  // ─── Handlers ─────────────────────────────────────────────────────────
  const handleSelectAnswer = (ans) => {
    if (testTerminated) return;
    setSelectedAnswers({ ...selectedAnswers, [currentQuestionIndex]: ans });
  };

  const goToQuestion = (index) => {
    if (testTerminated) return;
    // Track time on current question
    if (questionTimesRef.current[currentQuestionIndex] === undefined) {
      questionTimesRef.current[currentQuestionIndex] = 0;
    }
    setCurrentQuestionIndex(index);
  };

  const handleNext = () => goToQuestion(Math.min(currentQuestionIndex + 1, questions.length - 1));
  const handlePrevious = () => goToQuestion(Math.max(currentQuestionIndex - 1, 0));

  const handleSubmit = async () => {
    const unanswered = questions.length - Object.keys(selectedAnswers).length;
    if (unanswered > 0 && !confirm(`You have ${unanswered} unanswered question(s). Submit anyway?`)) return;
    await autoSubmitTest();
  };

  const calculateScore = () => {
    let correct = 0;
    questions.forEach((q, i) => {
      if (q.question_type === 'mcq') {
        if (selectedAnswers[i] === q.correct_answer_index) correct++;
      } else {
        // For open-ended, we might not have the assessment result yet or it might be stored in the answer record
        // This is a simplified frontend score; real score comes from backend completion
        if (selectedAnswers[i] && selectedAnswers[i].length > 10) correct++; 
      }
    });
    return { correct, total: questions.length, percentage: Math.round((correct / questions.length) * 100) };
  };

  const answeredCount = Object.keys(selectedAnswers).length;
  const elapsedMinutes = Math.floor((Date.now() - startTimeRef.current) / 60000);

  // ─── Loading / Error States ───────────────────────────────────────────
  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0a1a] text-white flex items-center justify-center">
        <div className="text-center">
          <Loader className="w-12 h-12 animate-spin mx-auto mb-4 text-purple-400" />
          <p className="text-lg">Loading assessment...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#0a0a1a] text-white flex items-center justify-center">
        <div className="text-center max-w-md">
          <AlertTriangle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-4 text-red-400">{error}</h2>
          <button onClick={() => navigate('/dashboard')} className="px-6 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg font-semibold transition-colors">
            Go to Dashboard
          </button>
        </div>
      </div>
    );
  }

  if (!questions.length) {
    return (
      <div className="min-h-screen bg-[#0a0a1a] text-white flex items-center justify-center">
        <div className="text-center max-w-md">
          <h2 className="text-2xl font-bold mb-4">No Questions Available</h2>
          <p className="text-gray-400 mb-6">Assessment ID: {assessmentId}</p>
          <button onClick={() => navigate('/dashboard')} className="px-6 py-3 bg-purple-600 rounded-lg font-semibold">
            Go to Dashboard
          </button>
        </div>
      </div>
    );
  }

  // ─── Results View ─────────────────────────────────────────────────────
  if (showResults) {
    const score = calculateScore();
    return (
      <div className="min-h-screen bg-[#0a0a1a] text-white">
        <header className="h-14 bg-[#111128] border-b border-white/10 flex items-center px-6">
          <Zap className="w-6 h-6 text-pink-500 mr-2" fill="#E945F5" />
          <span className="font-bold text-lg">Velocity</span>
          <span className="ml-auto text-sm text-gray-400">Assessment Complete</span>
        </header>
        <div className="max-w-4xl mx-auto px-6 py-12">
          <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
            className="bg-white/5 rounded-2xl border border-white/10 p-8 text-center">
            <div className="mb-8">
              {score.percentage >= 70 ? <CheckCircle className="w-24 h-24 text-green-400 mx-auto mb-4" /> : <XCircle className="w-24 h-24 text-red-400 mx-auto mb-4" />}
              <h2 className="text-4xl font-bold mb-2">{testTerminated ? 'Test Terminated' : 'Assessment Complete!'}</h2>
              {testTerminated && <p className="text-red-400 mb-2">Your test was auto-submitted due to exceeding the tab switch limit.</p>}
              <p className="text-gray-400">{assessment?.content_title || 'Assessment'}</p>
            </div>
            <div className="grid grid-cols-3 gap-6 mb-8">
              <div className="bg-white/5 rounded-xl p-6">
                <div className="text-4xl font-bold text-green-400 mb-2">{score.correct}</div>
                <div className="text-sm text-gray-400">Correct</div>
              </div>
              <div className="bg-white/5 rounded-xl p-6">
                <div className="text-4xl font-bold text-red-400 mb-2">{score.total - score.correct}</div>
                <div className="text-sm text-gray-400">Incorrect</div>
              </div>
              <div className="bg-white/5 rounded-xl p-6">
                <div className="text-4xl font-bold text-purple-400 mb-2">{score.percentage}%</div>
                <div className="text-sm text-gray-400">Score</div>
              </div>
            </div>
            <div className="space-y-4 mb-8 max-h-[50vh] overflow-y-auto pr-2">
              {questions.map((q, index) => {
                const ua = selectedAnswers[index];
                const isMCQ = q.question_type === 'mcq';
                const isCorrect = isMCQ ? ua === q.correct_answer_index : !!ua;
                return (
                  <div key={index} className={`bg-white/5 rounded-xl p-5 text-left border ${isCorrect ? 'border-green-500/40' : 'border-red-500/40'}`}>
                    <div className="flex items-start gap-3">
                      {isCorrect ? <CheckCircle className="w-5 h-5 text-green-400 mt-1 flex-shrink-0" /> : <XCircle className="w-5 h-5 text-red-400 mt-1 flex-shrink-0" />}
                      <div className="flex-1">
                        <p className="font-semibold mb-1">Q{index + 1}: {q.question_text}</p>
                        <div className="text-sm text-gray-400 mb-2">
                          Your answer: <span className={isCorrect ? 'text-green-400' : 'text-red-400'}>
                            {ua !== undefined ? (isMCQ ? q.options[ua] : ua) : 'Not answered'}
                          </span>
                        </div>
                        {isMCQ && !isCorrect && (
                          <p className="text-sm text-gray-400">Correct: <span className="text-green-400">{q.options[q.correct_answer_index]}</span></p>
                        )}
                        {!isMCQ && q.correct_answer && (
                          <div className="text-sm text-gray-400 mt-2 p-3 bg-white/5 rounded-lg border border-white/10">
                            <span className="text-purple-300 font-semibold block mb-1">Reference Answer:</span>
                            {q.correct_answer}
                          </div>
                        )}
                        {q.explanation && <p className="text-sm text-gray-300 mt-2 opacity-80">{q.explanation}</p>}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
            <button onClick={() => navigate('/dashboard')} className="px-8 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg font-semibold transition-colors">
              Back to Dashboard
            </button>
          </motion.div>
        </div>
      </div>
    );
  }

  // ─── AMCAT-Style Test Layout ──────────────────────────────────────────
  const currentQuestion = questions[currentQuestionIndex];

  return (
    <div className="h-screen bg-[#0a0a1a] text-white flex flex-col overflow-hidden select-none"
      onCopy={e => e.preventDefault()}
      onCut={e => e.preventDefault()}
      onPaste={e => e.preventDefault()}
      onContextMenu={e => e.preventDefault()}
      onDragStart={e => e.preventDefault()}
    >
      {/* ── Warning Overlay ── */}
      <AnimatePresence>
        {warningMessage && (
          <motion.div
            initial={{ y: -100, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -100, opacity: 0 }}
            className="fixed top-0 left-0 right-0 z-50 flex justify-center"
          >
            <div className={`mt-2 px-6 py-3 rounded-xl shadow-2xl flex items-center gap-3 max-w-lg ${testTerminated ? 'bg-red-600' : 'bg-orange-500'}`}>
              <AlertTriangle className="w-6 h-6 flex-shrink-0" />
              <span className="font-semibold text-sm">{warningMessage}</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Header Bar ── */}
      <header className="h-12 bg-[#111128] border-b border-white/10 flex items-center px-4 flex-shrink-0">
        <div className="flex items-center gap-2">
          <Zap className="w-5 h-5 text-pink-500" fill="#E945F5" />
          <span className="font-bold">Velocity Assessment</span>
        </div>
        <div className="flex items-center gap-4 ml-auto text-xs">
          <div className="flex items-center gap-1.5">
            <Shield className="w-4 h-4 text-green-400" />
            <span className="text-green-400">Proctored</span>
          </div>
          <div className={`flex items-center gap-1.5 ${tabSwitchCount >= 2 ? 'text-red-400' : tabSwitchCount >= 1 ? 'text-orange-400' : 'text-gray-400'}`}>
            <AlertTriangle className="w-4 h-4" />
            <span>Tab Switches: {tabSwitchCount}/3</span>
          </div>
          <div className="text-gray-400">
            Answered: {answeredCount}/{questions.length}
          </div>
          <div className="text-gray-400">
            Time: {elapsedMinutes}m
          </div>
        </div>
      </header>

      {/* ── Main Body ── */}
      <div className="flex flex-1 min-h-0">

        {/* ── LEFT: Question Panel (major portion) ── */}
        <div className="flex-1 flex flex-col min-w-0">

          {/* Question Number Bar */}
          <div className="h-10 bg-[#111128]/50 border-b border-white/5 flex items-center px-6 flex-shrink-0">
            <span className="text-sm font-semibold text-purple-300">
              Question {currentQuestionIndex + 1} of {questions.length}
            </span>
            {selectedAnswers[currentQuestionIndex] !== undefined && (
              <span className="ml-3 text-xs text-green-400 bg-green-400/10 px-2 py-0.5 rounded-full">
                ✓ Answered
              </span>
            )}
          </div>

          {/* Question Content */}
          <div className="flex-1 overflow-y-auto p-6 lg:p-8">
            <AnimatePresence mode="wait">
              <motion.div
                key={currentQuestionIndex}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.2 }}
              >
                {/* Question Text */}
                <h2 className="text-xl lg:text-2xl font-bold mb-8 leading-relaxed">
                  <span className="text-purple-400 mr-2">Q{currentQuestionIndex + 1}.</span>
                  {currentQuestion?.question_text}
                </h2>

                {/* Options / Answer Input */}
                <div className="space-y-4 max-w-3xl">
                  {currentQuestion?.question_type === 'mcq' ? (
                    currentQuestion?.options && Array.isArray(currentQuestion.options) ? (
                      currentQuestion.options.map((option, index) => {
                        const isSelected = selectedAnswers[currentQuestionIndex] === index;
                        return (
                          <button
                            key={index}
                            onClick={() => handleSelectAnswer(index)}
                            disabled={testTerminated}
                            className={`w-full p-4 rounded-xl text-left transition-all border flex items-start gap-3 ${isSelected
                                ? 'bg-purple-600/20 border-purple-500 shadow-lg shadow-purple-500/10'
                                : 'bg-white/[0.03] border-white/10 hover:border-purple-500/40 hover:bg-white/[0.06]'
                              } ${testTerminated ? 'opacity-50 cursor-not-allowed' : ''}`}
                          >
                            <span className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold flex-shrink-0 ${isSelected ? 'bg-purple-500 text-white' : 'bg-white/10 text-gray-400'
                              }`}>
                              {String.fromCharCode(65 + index)}
                            </span>
                            <span className="pt-1">{option}</span>
                          </button>
                        );
                      })
                    ) : (
                      <div className="text-red-400 p-4 bg-red-500/10 rounded-xl border border-red-500/30">
                        <p>Error: Question options not available</p>
                      </div>
                    )
                  ) : (
                    <div className="space-y-4">
                      <p className="text-sm text-gray-400 italic">Type your detailed technical answer below:</p>
                      <textarea
                        value={selectedAnswers[currentQuestionIndex] || ''}
                        onChange={(e) => handleSelectAnswer(e.target.value)}
                        disabled={testTerminated}
                        placeholder="Start typing your answer here..."
                        className="w-full h-64 p-5 rounded-xl bg-white/[0.03] border border-white/10 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-all outline-none resize-none text-gray-200 leading-relaxed font-mono text-sm"
                      />
                      <div className="flex justify-between items-center text-[10px] text-gray-500 uppercase tracking-widest">
                        <span>Characters: {(selectedAnswers[currentQuestionIndex] || '').length}</span>
                        <span>Min recommended: 20 characters</span>
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>
            </AnimatePresence>
          </div>

          {/* Navigation Footer */}
          <div className="h-16 bg-[#111128]/80 border-t border-white/10 flex items-center justify-between px-6 flex-shrink-0">
            <button
              onClick={handlePrevious}
              disabled={currentQuestionIndex === 0 || testTerminated}
              className="px-5 py-2 bg-white/10 hover:bg-white/15 rounded-lg font-semibold text-sm disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              ← Previous
            </button>

            <span className="text-sm text-gray-500">
              {answeredCount} of {questions.length} answered
            </span>

            {currentQuestionIndex === questions.length - 1 ? (
              <button
                onClick={handleSubmit}
                disabled={submitting || testTerminated}
                className="px-6 py-2 bg-green-600 hover:bg-green-700 rounded-lg font-semibold text-sm disabled:opacity-50 transition-colors flex items-center gap-2"
              >
                {submitting ? <Loader className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
                Submit Test
              </button>
            ) : (
              <button
                onClick={handleNext}
                disabled={testTerminated}
                className="px-5 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg font-semibold text-sm disabled:opacity-50 transition-colors"
              >
                Next →
              </button>
            )}
          </div>
        </div>

        {/* ── RIGHT: Sidebar (camera + navigator) ── */}
        <div className="w-72 lg:w-80 bg-[#0d0d20] border-l border-white/10 flex flex-col flex-shrink-0">

          {/* Camera Section (top) */}
          <div className="p-3 border-b border-white/10">
            <div className="flex items-center gap-2 mb-2 text-xs text-gray-400">
              {cameraError ? <CameraOff className="w-4 h-4 text-red-400" /> : <Camera className="w-4 h-4 text-green-400" />}
              <span>{cameraError ? 'Camera unavailable' : 'Proctoring Active'}</span>
              {!cameraError && <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse ml-auto" />}
            </div>
            <div className="aspect-[4/3] rounded-lg overflow-hidden bg-black/50 border border-white/10">
              {cameraError ? (
                <div className="w-full h-full flex items-center justify-center text-gray-600">
                  <div className="text-center">
                    <CameraOff className="w-8 h-8 mx-auto mb-2" />
                    <p className="text-xs">Camera not available</p>
                  </div>
                </div>
              ) : (
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className="w-full h-full object-cover mirror"
                  style={{ transform: 'scaleX(-1)' }}
                />
              )}
            </div>
          </div>

          {/* Question Navigator (bottom) */}
          <div className="flex-1 p-3 flex flex-col min-h-0">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Questions</span>
              <span className="text-xs text-gray-500">
                <span className="text-green-400">{answeredCount}</span> / {questions.length}
              </span>
            </div>

            <div className="flex-1 overflow-y-auto pr-1">
              <div className="grid grid-cols-5 gap-2">
                {questions.map((_, index) => {
                  const isAnswered = selectedAnswers[index] !== undefined;
                  const isCurrent = index === currentQuestionIndex;
                  return (
                    <button
                      key={index}
                      onClick={() => goToQuestion(index)}
                      disabled={testTerminated}
                      className={`
                        w-full aspect-square rounded-lg text-xs font-bold
                        flex items-center justify-center transition-all
                        ${isCurrent
                          ? 'bg-purple-600 text-white ring-2 ring-purple-400 ring-offset-1 ring-offset-[#0d0d20] scale-110'
                          : isAnswered
                            ? 'bg-green-600/80 text-white hover:bg-green-600'
                            : 'bg-red-600/40 text-red-200 hover:bg-red-600/60 border border-red-500/30'
                        }
                        ${testTerminated ? 'opacity-50 cursor-not-allowed' : ''}
                      `}
                    >
                      {index + 1}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Legend */}
            <div className="mt-3 pt-3 border-t border-white/10 flex flex-wrap gap-3 text-[10px] text-gray-500">
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded bg-green-600/80" />
                <span>Answered</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded bg-red-600/40 border border-red-500/30" />
                <span>Unanswered</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded bg-purple-600 ring-1 ring-purple-400" />
                <span>Current</span>
              </div>
            </div>

            {/* Submit Button at bottom */}
            <button
              onClick={handleSubmit}
              disabled={submitting || testTerminated}
              className="mt-3 w-full py-3 bg-green-600 hover:bg-green-700 rounded-lg font-semibold text-sm disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
            >
              {submitting ? <Loader className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
              Submit Test
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
