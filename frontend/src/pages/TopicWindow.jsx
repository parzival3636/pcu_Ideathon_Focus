import { useState, useRef, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Upload, Link as LinkIcon, FileText, Video, X, Plus, Zap, Send, ChevronLeft, ChevronRight, Loader2, AlertCircle, Download, ExternalLink, Clock, Coffee, CheckCircle, Play, Pause } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import 'bootstrap/dist/css/bootstrap.min.css';
import api, { studySessionAPI, contentAPI, chatAPI } from '../services/api';

// Import PDF viewer with correct CSS paths
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

// Set up PDF.js worker with a reliable CDN
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

export default function TopicWindow() {
  const navigate = useNavigate();
  const { topicId, sessionId } = useParams();

  // Session state
  const [session, setSession] = useState(null);
  const [isOnBreak, setIsOnBreak] = useState(false);
  const [breakTimeLeft, setBreakTimeLeft] = useState(0);
  const [sessionTime, setSessionTime] = useState(0);
  const [isPaused, setIsPaused] = useState(false);

  // Timers
  const sessionTimer = useRef(null);
  const breakTimer = useRef(null);

  // Refs
  const whiteboardRef = useRef(null);
  const whiteboardInstance = useRef(null);
  const fileInputRef = useRef(null);

  const [showAddContent, setShowAddContent] = useState(false);
  const [contentType, setContentType] = useState(null);
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [currentVideo, setCurrentVideo] = useState(null);
  const [currentContent, setCurrentContent] = useState(null);
  const [contents, setContents] = useState([]);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [docError, setDocError] = useState(null);
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);

  // MCQ state
  const [generatedQuestions, setGeneratedQuestions] = useState([]);
  const [processingContent, setProcessingContent] = useState(false);
  const [contentIdForMCQ, setContentIdForMCQ] = useState(null);

  // Resizable panel states
  const [leftWidth, setLeftWidth] = useState(256);
  const [rightWidth, setRightWidth] = useState(384);
  const [whiteboardHeight, setWhiteboardHeight] = useState(50);
  const [isDraggingLeft, setIsDraggingLeft] = useState(false);
  const [isDraggingRight, setIsDraggingRight] = useState(false);
  const [isDraggingHorizontal, setIsDraggingHorizontal] = useState(false);

  // Initialize Whiteboard.team
  useEffect(() => {
    if (whiteboardRef.current && !whiteboardInstance.current && window.api) {
      try {
        whiteboardInstance.current = new window.api.WhiteboardTeam(whiteboardRef.current, {
          clientId: 'b6289bc542b7a2e592bb5f232c94114e',
          boardCode: `velocity-${topicId || sessionId}-${Date.now()}`
        });
      } catch (error) {
        console.error('Whiteboard initialization error:', error);
      }
    }
  }, [topicId, sessionId]);

  // Load session if sessionId is provided
  useEffect(() => {
    if (sessionId) {
      loadSession();
    }
    return () => {
      if (sessionTimer.current) clearInterval(sessionTimer.current);
      if (breakTimer.current) clearInterval(breakTimer.current);
    };
  }, [sessionId]);

  // Session timer
  useEffect(() => {
    if (session && !isOnBreak && !isPaused) {
      sessionTimer.current = setInterval(() => {
        setSessionTime(prev => prev + 1);
      }, 1000);
    } else {
      if (sessionTimer.current) clearInterval(sessionTimer.current);
    }

    return () => {
      if (sessionTimer.current) clearInterval(sessionTimer.current);
    };
  }, [session, isOnBreak, isPaused]);

  // Break timer
  useEffect(() => {
    if (isOnBreak && breakTimeLeft > 0) {
      breakTimer.current = setInterval(() => {
        setBreakTimeLeft(prev => {
          if (prev <= 1) {
            handleEndBreak();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } else {
      if (breakTimer.current) clearInterval(breakTimer.current);
    }

    return () => {
      if (breakTimer.current) clearInterval(breakTimer.current);
    };
  }, [isOnBreak, breakTimeLeft]);

  const loadSession = async () => {
    try {
      const response = await studySessionAPI.get(sessionId);
      setSession(response.data);
    } catch (err) {
      console.error('Failed to load session:', err);
    }
  };

  const formatTime = (seconds) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hrs > 0) {
      return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleTogglePause = () => {
    setIsPaused(!isPaused);
  };

  const handleStartBreak = async () => {
    if (!sessionId) return;
    try {
      const response = await studySessionAPI.startBreak(sessionId);
      setIsOnBreak(true);
      setBreakTimeLeft(response.data.break_duration_seconds || 300);
    } catch (err) {
      console.error('Failed to start break:', err);
    }
  };

  const handleEndBreak = async () => {
    if (!sessionId) return;
    try {
      await studySessionAPI.endBreak(sessionId);
      setIsOnBreak(false);
      setBreakTimeLeft(0);
    } catch (err) {
      console.error('Failed to end break:', err);
    }
  };

  const [completing, setCompleting] = useState(false);

  const handleCompleteSession = async () => {
    if (!sessionId || completing) return;
    setCompleting(true);
    try {
      await studySessionAPI.complete(sessionId);
    } catch (err) {
      console.error('Failed to complete session:', err);
      // Still navigate to dashboard even if already completed
    }
    navigate('/dashboard', {
      state: { message: 'Session complete! Your test will be ready shortly.' }
    });
  };

  // Handle resizing
  useEffect(() => {
    const handleMouseMove = (e) => {
      if (isDraggingLeft) {
        const newWidth = Math.max(200, Math.min(500, e.clientX));
        setLeftWidth(newWidth);
      }
      if (isDraggingRight) {
        const newWidth = Math.max(300, Math.min(600, window.innerWidth - e.clientX));
        setRightWidth(newWidth);
      }
      if (isDraggingHorizontal) {
        const container = document.querySelector('.whiteboard-chat-container');
        if (container) {
          const rect = container.getBoundingClientRect();
          const newHeight = ((e.clientY - rect.top) / rect.height) * 100;
          setWhiteboardHeight(Math.max(30, Math.min(70, newHeight)));
        }
      }
    };

    const handleMouseUp = () => {
      setIsDraggingLeft(false);
      setIsDraggingRight(false);
      setIsDraggingHorizontal(false);
    };

    if (isDraggingLeft || isDraggingRight || isDraggingHorizontal) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = isDraggingHorizontal ? 'ns-resize' : 'ew-resize';
      document.body.style.userSelect = 'none';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isDraggingLeft, isDraggingRight, isDraggingHorizontal]);

  // Cleanup object URLs when content changes
  useEffect(() => {
    return () => {
      contents.forEach(content => {
        if (content.url && content.url.startsWith('blob:')) {
          URL.revokeObjectURL(content.url);
        }
      });
    };
  }, [contents]);

  const handleAddYouTube = async () => {
    if (youtubeUrl.trim()) {
      const embedUrl = convertToEmbedUrl(youtubeUrl);
      const tempId = Date.now();

      // Step 1: Immediately show video (close modal, display video)
      const newContent = {
        id: tempId,
        type: 'youtube',
        url: embedUrl,
        title: 'YouTube Video',
        loading: true
      };

      setContents([...contents, newContent]);
      setCurrentContent(newContent);
      setCurrentVideo(embedUrl);
      setYoutubeUrl('');
      setShowAddContent(false);
      setContentType(null);

      // Step 2: Process in background (upload and get transcript only, NO MCQ generation)
      setProcessingContent(true);

      // Background processing
      (async () => {
        try {
          // Upload content and fetch transcript
          // Send JSON directly (no file, just text fields — no multipart needed)
          const uploadResponse = await api.post('/content/upload/', {
            title: 'YouTube Video',
            content_type: 'youtube',
            url: youtubeUrl
          });

          const contentId = uploadResponse.data.id;
          setContentIdForMCQ(contentId);

          // Update session with this content
          if (sessionId) {
            await studySessionAPI.updateContent(sessionId, contentId);
            console.log(`✅ Session ${sessionId} updated with content ${contentId}`);
          }

          // Update content with backend ID
          setContents(prevContents =>
            prevContents.map(c =>
              c.id === tempId
                ? { ...c, backendId: contentId, loading: false, title: uploadResponse.data.title || 'YouTube Video' }
                : c
            )
          );

          // Silent success - content uploaded and ready
          console.log(`✅ Content uploaded successfully (ID: ${contentId})`);

        } catch (error) {
          console.error('Background processing failed:', error);

          // Update content to show processing failed
          setContents(prevContents =>
            prevContents.map(c =>
              c.id === tempId
                ? { ...c, loading: false, error: true }
                : c
            )
          );
        } finally {
          setProcessingContent(false);
        }
      })();
    }
  };

  const convertToEmbedUrl = (url) => {
    let videoId = '';

    if (url.includes('youtube.com/watch?v=')) {
      videoId = url.split('v=')[1]?.split('&')[0];
    } else if (url.includes('youtu.be/')) {
      videoId = url.split('youtu.be/')[1]?.split('?')[0];
    } else if (url.includes('youtube.com/embed/')) {
      return url;
    }

    return videoId ? `https://www.youtube.com/embed/${videoId}?rel=0` : url;
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (file) {
      setLoading(true);
      setDocError(null);

      try {
        // Small delay to show loading state
        await new Promise(resolve => setTimeout(resolve, 500));

        const fileUrl = URL.createObjectURL(file);

        const newContent = {
          id: Date.now(),
          type: contentType,
          url: fileUrl,
          file: file,
          title: file.name,
          fileType: file.type
        };

        setContents([...contents, newContent]);
        setCurrentContent(newContent);
        setCurrentVideo(null);
        setShowAddContent(false);
        setContentType(null);
      } catch (error) {
        console.error('File upload error:', error);
        setDocError('Failed to load file. Please try again.');
      } finally {
        setLoading(false);
      }
    }
  };

  const handleContentClick = (content) => {
    setCurrentContent(content);
    setDocError(null);
    setPageNumber(1);
    setPdfLoading(content.type === 'pdf');
    if (content.type === 'youtube') {
      setCurrentVideo(content.url);
    } else {
      setCurrentVideo(null);
    }
  };

  const handleSendMessage = async () => {
    if (!chatInput.trim()) return;
    const userMsg = chatInput.trim();
    setChatMessages(prev => [...prev, { id: Date.now(), text: userMsg, sender: 'user' }]);
    setChatInput('');

    // Show typing indicator
    const typingId = Date.now() + 1;
    setChatMessages(prev => [...prev, { id: typingId, text: '...', sender: 'ai', isTyping: true }]);

    try {
      const response = await chatAPI.sendQuery(sessionId, userMsg);
      const data = response.data;
      // Remove typing indicator and add real response
      setChatMessages(prev => [
        ...prev.filter(m => m.id !== typingId),
        {
          id: Date.now() + 2,
          text: data.response || data.fallback_response || 'I could not process that question. Please try again.',
          sender: 'ai',
          isFallback: data.is_fallback || false
        }
      ]);
    } catch (err) {
      console.error('Chat error:', err);
      setChatMessages(prev => [
        ...prev.filter(m => m.id !== typingId),
        {
          id: Date.now() + 2,
          text: err.response?.data?.error || 'Failed to get a response. Please check that the session is active and try again.',
          sender: 'ai',
          isError: true
        }
      ]);
    }
  };

  function onDocumentLoadSuccess({ numPages }) {
    setNumPages(numPages);
    setPdfLoading(false);
    setDocError(null);
  }

  function onDocumentLoadError(error) {
    console.error('PDF load error:', error);
    setPdfLoading(false);
    setDocError('Failed to load PDF. The file might be corrupted or password protected.');
  }

  // Render PDF using react-pdf
  const renderPDF = () => {
    if (!currentContent?.url) return null;

    return (
      <div className="h-full flex flex-col">
        <div className="bg-gray-800 p-2 flex items-center justify-between">
          <span className="text-white text-sm truncate">{currentContent.title}</span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPageNumber(Math.max(1, pageNumber - 1))}
              disabled={pageNumber <= 1 || pdfLoading}
              className="p-1 rounded bg-white/10 hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-xs text-white">
              {pdfLoading ? 'Loading...' : `Page ${pageNumber} of ${numPages || '?'}`}
            </span>
            <button
              onClick={() => setPageNumber(Math.min(numPages || 1, pageNumber + 1))}
              disabled={pageNumber >= (numPages || 1) || pdfLoading}
              className="p-1 rounded bg-white/10 hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
        <div className="flex-1 overflow-auto p-4 bg-gray-900">
          {pdfLoading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <Loader2 className="w-12 h-12 text-pink-500 animate-spin mx-auto mb-4" />
                <p className="text-gray-400">Loading PDF...</p>
              </div>
            </div>
          ) : docError ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center p-8 max-w-md">
                <AlertCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
                <h3 className="text-xl font-bold text-white mb-2">Failed to Load PDF</h3>
                <p className="text-gray-400 mb-6">{docError}</p>
                <a
                  href={currentContent.url}
                  download={currentContent.title}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-pink-500 to-blue-500 rounded-lg font-semibold hover:shadow-lg transition-all"
                >
                  <Download className="w-4 h-4" />
                  Download Instead
                </a>
              </div>
            </div>
          ) : (
            <Document
              file={currentContent.url}
              onLoadSuccess={onDocumentLoadSuccess}
              onLoadError={onDocumentLoadError}
              loading={null} // We handle loading state ourselves
            >
              <Page
                pageNumber={pageNumber}
                renderTextLayer={true}
                renderAnnotationLayer={true}
                className="mx-auto"
                width={Math.min(800, window.innerWidth * 0.5)}
                loading={
                  <div className="flex items-center justify-center p-8">
                    <Loader2 className="w-8 h-8 text-pink-500 animate-spin" />
                  </div>
                }
              />
            </Document>
          )}
        </div>
      </div>
    );
  };

  // Render unsupported file types
  const renderUnsupportedFile = (type) => {
    if (!currentContent?.url) return null;

    return (
      <div className="h-full flex flex-col">
        <div className="bg-gray-800 p-2 flex items-center justify-between">
          <span className="text-white text-sm truncate">{currentContent.title}</span>
          <div className="flex items-center gap-2">
            <a
              href={currentContent.url}
              target="_blank"
              rel="noopener noreferrer"
              className="p-1 rounded bg-white/10 hover:bg-white/20"
              title="Open in new tab"
            >
              <ExternalLink className="w-4 h-4" />
            </a>
            <a
              href={currentContent.url}
              download={currentContent.title}
              className="p-1 rounded bg-white/10 hover:bg-white/20"
              title="Download"
            >
              <Download className="w-4 h-4" />
            </a>
          </div>
        </div>
        <div className="flex-1 bg-gray-900 flex items-center justify-center">
          <div className="text-center p-8 max-w-md">
            <AlertCircle className="w-16 h-16 text-yellow-400 mx-auto mb-4" />
            <h3 className="text-xl font-bold text-white mb-2">
              {type === 'ppt' ? 'PowerPoint Preview' : 'Word Document Preview'}
            </h3>
            <p className="text-gray-400 mb-6">
              {type === 'ppt'
                ? 'PowerPoint files cannot be previewed directly in the browser.'
                : 'Word documents cannot be previewed directly in the browser.'}
            </p>
            <div className="flex gap-3 justify-center">
              <a
                href={currentContent.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-pink-500 to-blue-500 rounded-lg font-semibold hover:shadow-lg transition-all"
              >
                <ExternalLink className="w-4 h-4" />
                Open in Tab
              </a>
              <a
                href={currentContent.url}
                download={currentContent.title}
                className="inline-flex items-center gap-2 px-4 py-2 bg-white/10 rounded-lg font-semibold hover:bg-white/20 transition-all"
              >
                <Download className="w-4 h-4" />
                Download
              </a>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-950 to-slate-950 text-white">
      {/* Header */}
      <header className="border-b border-white/10 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-full px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="p-2 hover:bg-white/10 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <Zap className="w-8 h-8 text-pink-500" fill="#E945F5" />
            <span className="text-xl font-bold">Velocity</span>

            {/* Timer Display (only show if session exists) */}
            {sessionId && (
              <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-white/10">
                <Clock className="w-4 h-4" />
                <span className="text-sm font-mono">{formatTime(sessionTime)}</span>
              </div>
            )}
          </div>

          <div className="flex items-center gap-3">
            {/* Timer Controls (only show if session exists) */}
            {sessionId && (
              <>
                {/* Pause/Play Button */}
                <button
                  onClick={handleTogglePause}
                  className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                  title={isPaused ? 'Resume' : 'Pause'}
                >
                  {isPaused ? <Play className="w-5 h-5" /> : <Pause className="w-5 h-5" />}
                </button>

                {/* Break Button */}
                {!isOnBreak ? (
                  <button
                    onClick={handleStartBreak}
                    className="flex items-center gap-2 px-4 py-2 bg-white/10 rounded-lg hover:bg-white/20 transition-colors"
                  >
                    <Coffee className="w-5 h-5" />
                    <span>Break</span>
                  </button>
                ) : (
                  <div className="flex items-center gap-2 px-4 py-2 bg-orange-500/20 rounded-lg">
                    <Coffee className="w-5 h-5 text-orange-400" />
                    <span className="text-orange-400">{formatTime(breakTimeLeft)}</span>
                  </div>
                )}

                {/* Complete Button */}
                <button
                  onClick={handleCompleteSession}
                  className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-500 rounded-lg hover:shadow-lg transition-all"
                >
                  <CheckCircle className="w-5 h-5" />
                  <span>Complete</span>
                </button>
              </>
            )}

            {/* Add Content Button */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setShowAddContent(true)}
              className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-pink-500 to-blue-500 rounded-lg font-semibold"
            >
              <Plus className="w-5 h-5" />
              Add Content
            </motion.button>
          </div>
        </div>
      </header>

      {/* Main Layout */}
      <div className="flex h-[calc(100vh-73px)]">
        {/* Left Sidebar - Content List */}
        <div
          className="border-r border-white/10 bg-black/20 backdrop-blur-sm overflow-y-auto"
          style={{ width: `${leftWidth}px` }}
        >
          <div className="p-4">
            <h3 className="text-sm font-semibold text-gray-400 mb-3">CONTENT</h3>

            {contents.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-sm text-gray-500">No content yet</p>
              </div>
            ) : (
              <div className="space-y-2">
                {/* YouTube Videos Section */}
                {contents.filter(c => c.type === 'youtube').length > 0 && (
                  <div className="mb-4">
                    <p className="text-xs text-gray-500 mb-2">Videos</p>
                    {contents.filter(c => c.type === 'youtube').map((content) => (
                      <motion.button
                        key={content.id}
                        whileHover={{ x: 4 }}
                        onClick={() => handleContentClick(content)}
                        className={`w-full p-3 rounded-lg border transition-all text-left ${currentContent?.id === content.id
                          ? 'bg-pink-500/20 border-pink-500/50'
                          : 'bg-white/5 border-white/10 hover:border-pink-500/30'
                          }`}
                      >
                        <div className="flex items-center gap-2">
                          <Video className="w-4 h-4 text-red-400 flex-shrink-0" />
                          <span className="text-sm truncate">{content.title}</span>
                        </div>
                      </motion.button>
                    ))}
                  </div>
                )}

                {/* PDF Section */}
                {contents.filter(c => c.type === 'pdf').length > 0 && (
                  <div className="mb-4">
                    <p className="text-xs text-gray-500 mb-2">PDFs</p>
                    {contents.filter(c => c.type === 'pdf').map((content) => (
                      <motion.button
                        key={content.id}
                        whileHover={{ x: 4 }}
                        onClick={() => handleContentClick(content)}
                        className={`w-full p-3 rounded-lg border transition-all text-left ${currentContent?.id === content.id
                          ? 'bg-pink-500/20 border-pink-500/50'
                          : 'bg-white/5 border-white/10 hover:border-pink-500/30'
                          }`}
                      >
                        <div className="flex items-center gap-2">
                          <FileText className="w-4 h-4 text-blue-400 flex-shrink-0" />
                          <span className="text-sm truncate">{content.title}</span>
                        </div>
                      </motion.button>
                    ))}
                  </div>
                )}

                {/* Word Section */}
                {contents.filter(c => c.type === 'word').length > 0 && (
                  <div className="mb-4">
                    <p className="text-xs text-gray-500 mb-2">Word Documents</p>
                    {contents.filter(c => c.type === 'word').map((content) => (
                      <motion.button
                        key={content.id}
                        whileHover={{ x: 4 }}
                        onClick={() => handleContentClick(content)}
                        className={`w-full p-3 rounded-lg border transition-all text-left ${currentContent?.id === content.id
                          ? 'bg-pink-500/20 border-pink-500/50'
                          : 'bg-white/5 border-white/10 hover:border-pink-500/30'
                          }`}
                      >
                        <div className="flex items-center gap-2">
                          <FileText className="w-4 h-4 text-blue-500 flex-shrink-0" />
                          <span className="text-sm truncate">{content.title}</span>
                        </div>
                      </motion.button>
                    ))}
                  </div>
                )}

                {/* PPT Section */}
                {contents.filter(c => c.type === 'ppt').length > 0 && (
                  <div>
                    <p className="text-xs text-gray-500 mb-2">Presentations</p>
                    {contents.filter(c => c.type === 'ppt').map((content) => (
                      <motion.button
                        key={content.id}
                        whileHover={{ x: 4 }}
                        onClick={() => handleContentClick(content)}
                        className={`w-full p-3 rounded-lg border transition-all text-left ${currentContent?.id === content.id
                          ? 'bg-pink-500/20 border-pink-500/50'
                          : 'bg-white/5 border-white/10 hover:border-pink-500/30'
                          }`}
                      >
                        <div className="flex items-center gap-2">
                          <Upload className="w-4 h-4 text-orange-400 flex-shrink-0" />
                          <span className="text-sm truncate">{content.title}</span>
                        </div>
                      </motion.button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Left Resize Handle */}
        <div
          className="w-1 hover:w-1.5 bg-transparent hover:bg-pink-500/50 cursor-ew-resize transition-all relative group"
          onMouseDown={() => setIsDraggingLeft(true)}
        >
          <div className="absolute inset-y-0 -left-1 -right-1" />
        </div>

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col lg:flex-row min-w-0">
          {/* Left: Video/PDF/PPT Player */}
          <div className="flex-1 p-6 overflow-y-auto">
            <div className="max-w-4xl mx-auto">
              {currentContent ? (
                <>
                  {currentContent.type === 'youtube' && (
                    <div className="mb-6">
                      <div className="ratio ratio-16x9">
                        <iframe
                          src={currentContent.url}
                          title="YouTube video"
                          allowFullScreen
                          className="rounded-xl"
                        />
                      </div>
                    </div>
                  )}

                  {currentContent.type === 'pdf' && (
                    <div className="bg-white rounded-xl overflow-hidden mb-6" style={{ height: '80vh' }}>
                      <div className="bg-gray-800 p-4 flex items-center justify-between">
                        <span className="text-white text-sm">{currentContent.title}</span>
                      </div>
                      <iframe
                        src={currentContent.url}
                        className="w-full"
                        style={{ height: 'calc(100% - 60px)' }}
                        title={currentContent.title}
                      />
                    </div>
                  )}

                  {currentContent.type === 'ppt' && (
                    <div className="bg-white/5 rounded-xl overflow-hidden mb-6" style={{ height: '70vh' }}>
                      {renderUnsupportedFile('ppt')}
                    </div>
                  )}

                  {currentContent.type === 'word' && (
                    <div className="bg-white/5 rounded-xl overflow-hidden mb-6" style={{ height: '70vh' }}>
                      {renderUnsupportedFile('word')}
                    </div>
                  )}
                </>
              ) : (
                <div className="aspect-video bg-black/50 rounded-xl flex items-center justify-center mb-6">
                  <div className="text-center">
                    <Video className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                    <p className="text-gray-400">No content selected</p>
                    <button
                      onClick={() => setShowAddContent(true)}
                      className="mt-4 text-pink-400 hover:text-pink-300 transition-colors text-sm"
                    >
                      Add your first content
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right Resize Handle */}
          <div
            className="w-1 hover:w-1.5 bg-transparent hover:bg-pink-500/50 cursor-ew-resize transition-all relative group"
            onMouseDown={() => setIsDraggingRight(true)}
          >
            <div className="absolute inset-y-0 -left-1 -right-1" />
          </div>

          {/* Right: Whiteboard & Chat */}
          <div
            className="border-l border-white/10 flex flex-col whiteboard-chat-container"
            style={{ width: `${rightWidth}px` }}
          >
            {/* Whiteboard */}
            <div
              className="border-b border-white/10 flex flex-col"
              style={{ height: `${whiteboardHeight}%` }}
            >
              <div className="p-4 border-b border-white/10 flex items-center justify-between bg-black/20">
                <h3 className="font-semibold">Whiteboard</h3>
              </div>
              <div
                ref={whiteboardRef}
                id="wt-container"
                style={{ width: '100%', height: 'calc(100% - 57px)' }}
                className="bg-white"
              />
            </div>

            {/* Horizontal Resize Handle */}
            <div
              className="h-1 hover:h-1.5 bg-transparent hover:bg-pink-500/50 cursor-ns-resize transition-all relative group"
              onMouseDown={() => setIsDraggingHorizontal(true)}
            >
              <div className="absolute inset-x-0 -top-1 -bottom-1" />
            </div>

            {/* Chat Interface */}
            <div
              className="flex flex-col bg-black/20"
              style={{ height: `${100 - whiteboardHeight}%` }}
            >
              <div className="p-4 border-b border-white/10">
                <h3 className="font-semibold">Ask Questions</h3>
              </div>
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {chatMessages.length === 0 ? (
                  <p className="text-sm text-gray-500 text-center py-8">
                    Ask questions about the content
                  </p>
                ) : (
                  chatMessages.map((msg) => (
                    <div
                      key={msg.id}
                      className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[80%] px-4 py-2 rounded-lg ${msg.sender === 'user'
                          ? 'bg-gradient-to-r from-pink-500 to-blue-500'
                          : 'bg-white/10'
                          }`}
                      >
                        <p className="text-sm">{msg.text}</p>
                      </div>
                    </div>
                  ))
                )}
              </div>
              <div className="p-4 border-t border-white/10">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                    placeholder="Type your question..."
                    className="flex-1 px-4 py-2 bg-white/5 border border-white/10 rounded-lg focus:border-pink-500/50 focus:outline-none text-sm"
                  />
                  <button
                    onClick={handleSendMessage}
                    className="p-2 bg-gradient-to-r from-pink-500 to-blue-500 rounded-lg hover:shadow-lg hover:shadow-pink-500/50 transition-all"
                  >
                    <Send className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Add Content Modal */}
      <AnimatePresence>
        {showAddContent && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-6"
            onClick={() => {
              setShowAddContent(false);
              setContentType(null);
            }}
          >
            <motion.div
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.9 }}
              onClick={(e) => e.stopPropagation()}
              className="w-full max-w-2xl bg-gradient-to-br from-slate-900 to-purple-900/50 rounded-2xl border border-white/10"
            >
              <div className="p-6 border-b border-white/10 flex items-center justify-between">
                <h2 className="text-2xl font-bold">Add Content</h2>
                <button onClick={() => setShowAddContent(false)} className="p-2 hover:bg-white/10 rounded-lg">
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="p-6">
                {!contentType ? (
                  <div className="space-y-4">
                    <button
                      onClick={() => setContentType('youtube')}
                      className="w-full p-6 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 hover:border-pink-500/50 transition-all flex items-center gap-4"
                    >
                      <div className="p-4 rounded-xl bg-red-500/20">
                        <Video className="w-8 h-8 text-red-400" />
                      </div>
                      <div className="text-left">
                        <h3 className="text-lg font-bold">YouTube Video</h3>
                        <p className="text-sm text-gray-400">Paste a YouTube link</p>
                      </div>
                    </button>

                    <button
                      onClick={() => setContentType('word')}
                      className="w-full p-6 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 hover:border-pink-500/50 transition-all flex items-center gap-4"
                    >
                      <div className="p-4 rounded-xl bg-blue-500/20">
                        <FileText className="w-8 h-8 text-blue-500" />
                      </div>
                      <div className="text-left">
                        <h3 className="text-lg font-bold">Word Document</h3>
                        <p className="text-sm text-gray-400">Upload a Word file</p>
                      </div>
                    </button>

                    <button
                      onClick={() => setContentType('pdf')}
                      className="w-full p-6 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 hover:border-pink-500/50 transition-all flex items-center gap-4"
                    >
                      <div className="p-4 rounded-xl bg-blue-500/20">
                        <FileText className="w-8 h-8 text-blue-400" />
                      </div>
                      <div className="text-left">
                        <h3 className="text-lg font-bold">PDF Document</h3>
                        <p className="text-sm text-gray-400">Upload a PDF file</p>
                      </div>
                    </button>

                    <button
                      onClick={() => setContentType('ppt')}
                      className="w-full p-6 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 hover:border-pink-500/50 transition-all flex items-center gap-4"
                    >
                      <div className="p-4 rounded-xl bg-orange-500/20">
                        <Upload className="w-8 h-8 text-orange-400" />
                      </div>
                      <div className="text-left">
                        <h3 className="text-lg font-bold">PowerPoint</h3>
                        <p className="text-sm text-gray-400">Upload PPT/PPTX</p>
                      </div>
                    </button>
                  </div>
                ) : contentType === 'youtube' ? (
                  <div className="space-y-6">
                    <button onClick={() => setContentType(null)} className="text-sm text-gray-400 hover:text-white">
                      ← Back
                    </button>

                    <div>
                      <label className="block text-sm font-medium mb-2">YouTube URL</label>
                      <div className="relative">
                        <LinkIcon className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                        <input
                          type="text"
                          value={youtubeUrl}
                          onChange={(e) => setYoutubeUrl(e.target.value)}
                          onKeyPress={(e) => e.key === 'Enter' && youtubeUrl.trim() && handleAddYouTube()}
                          placeholder="https://youtube.com/watch?v=..."
                          className="w-full pl-12 pr-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:border-pink-500/50 focus:outline-none"
                        />
                      </div>
                      <p className="text-xs text-gray-400 mt-2">
                        Questions will be generated in the background
                      </p>
                    </div>

                    <button
                      onClick={handleAddYouTube}
                      disabled={!youtubeUrl.trim()}
                      className="w-full py-3 bg-gradient-to-r from-pink-500 to-blue-500 rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Confirm
                    </button>
                  </div>
                ) : (
                  <div className="space-y-6">
                    <button onClick={() => setContentType(null)} className="text-sm text-gray-400 hover:text-white">
                      ← Back
                    </button>

                    <input
                      ref={fileInputRef}
                      type="file"
                      accept={
                        contentType === 'pdf' ? '.pdf' :
                          contentType === 'ppt' ? '.ppt,.pptx' :
                            '.doc,.docx'
                      }
                      onChange={handleFileUpload}
                      className="hidden"
                    />

                    <div
                      onClick={() => fileInputRef.current?.click()}
                      className="border-2 border-dashed border-white/20 rounded-xl p-12 text-center hover:border-pink-500/50 cursor-pointer transition-all"
                    >
                      {loading ? (
                        <>
                          <Loader2 className="w-12 h-12 text-pink-400 mx-auto mb-4 animate-spin" />
                          <p className="text-gray-400">Uploading...</p>
                        </>
                      ) : (
                        <>
                          <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                          <p className="text-gray-400">
                            Click to select {
                              contentType === 'pdf' ? 'PDF' :
                                contentType === 'ppt' ? 'PowerPoint' :
                                  'Word'
                            } file
                          </p>
                          <p className="text-sm text-gray-500 mt-2">
                            {contentType === 'pdf' ? 'Supported: .pdf' :
                              contentType === 'ppt' ? 'Supported: .ppt, .pptx' :
                                'Supported: .doc, .docx'}
                          </p>
                        </>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}