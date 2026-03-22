import { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import {
  Zap,
  Mail,
  Lock,
  Sparkles,
  Eye,
  EyeOff,
  ArrowRight,
  Shield,
  Star,
  AlertCircle,
  CheckCircle
} from 'lucide-react';
import { motion } from 'framer-motion';
import Particles from 'react-tsparticles';
import { loadSlim } from 'tsparticles-slim';
import Typewriter from 'typewriter-effect';
import { useCallback } from 'react';
import { authenticationAPI } from '../services/api';
import { useLanguage } from '../i18n/LanguageContext';

export default function SignIn() {
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useLanguage();
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const cardRef = useRef(null);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState(location.state?.message || '');

  // Mouse move effect for 3D tilt
  useEffect(() => {
    const handleMouseMove = (e) => {
      if (cardRef.current) {
        const rect = cardRef.current.getBoundingClientRect();
        setMousePosition({
          x: (e.clientX - rect.left) / rect.width - 0.5,
          y: (e.clientY - rect.top) / rect.height - 0.5
        });
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMessage('');

    // Validation
    if (!formData.email.trim()) {
      setError(t('signInPage.pleaseEnterEmail'));
      return;
    }
    if (!formData.password) {
      setError(t('signInPage.pleaseEnterPassword'));
      return;
    }

    setIsLoading(true);

    try {
      await authenticationAPI.signin(formData);
      // On success, navigate to dashboard
      navigate('/dashboard');
    } catch (err) {
      console.error('Signin error:', err);
      setError(
        err.response?.data?.error ||
        err.response?.data?.message ||
        t('signInPage.invalidCredentials')
      );
    } finally {
      setIsLoading(false);
    }
  };

  // Particles initialization
  const particlesInit = useCallback(async (engine) => {
    await loadSlim(engine);
  }, []);

  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white flex items-center justify-center p-6 relative overflow-hidden">
      {/* Advanced Particle Background */}
      <Particles
        id="tsparticles"
        init={particlesInit}
        className="absolute inset-0"
        options={{
          background: {
            color: {
              value: "transparent",
            },
          },
          fpsLimit: 60,
          particles: {
            color: {
              value: ["#ff0066", "#00ff99", "#00ccff", "#9933ff"],
            },
            links: {
              color: "#ffffff",
              distance: 150,
              enable: true,
              opacity: 0.1,
              width: 1,
            },
            move: {
              direction: "none",
              enable: true,
              outModes: {
                default: "bounce",
              },
              random: true,
              speed: 1,
              straight: false,
            },
            number: {
              density: {
                enable: true,
                area: 800,
              },
              value: 80,
            },
            opacity: {
              value: 0.3,
              random: true,
              animation: {
                enable: true,
                speed: 1,
                minimumValue: 0.1,
                sync: false
              }
            },
            shape: {
              type: ["circle", "triangle", "star"],
            },
            size: {
              value: { min: 1, max: 3 },
              random: true,
              animation: {
                enable: true,
                speed: 2,
                minimumValue: 0.5,
                sync: false
              }
            },
          },
          detectRetina: true,
        }}
      />

      {/* Animated gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-purple-900/20 via-pink-900/20 to-blue-900/20 animate-gradient-xy" />

      {/* Floating orbs */}
      <div className="absolute top-20 left-20 w-96 h-96 bg-purple-600 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob" />
      <div className="absolute top-40 right-20 w-96 h-96 bg-pink-600 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000" />
      <div className="absolute bottom-20 left-1/2 w-96 h-96 bg-blue-600 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000" />

      {/* Grid overlay with animation */}
      <div
        className="absolute inset-0 opacity-30"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M54 1h4v4h-4zM6 1h4v4H6zM30 1h4v4h-4zM54 29h4v4h-4zM6 29h4v4H6zM30 29h4v4h-4zM54 57h4v4h-4zM6 57h4v4H6zM30 57h4v4h-4z' fill='rgba(255,255,255,0.1)' fill-rule='evenodd'/%3E%3C/svg%3E")`,
          backgroundRepeat: 'repeat',
          animation: 'slide 20s linear infinite'
        }}
      />

      {/* Vignette effect */}
      <div className="absolute inset-0 bg-radial-gradient from-transparent to-gray-950/80 pointer-events-none" />

      {/* Noise texture */}
      <div className="absolute inset-0 opacity-5 mix-blend-overlay pointer-events-none"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")`,
          backgroundRepeat: 'repeat',
          backgroundSize: '200px 200px'
        }}
      />

      <motion.div
        initial="hidden"
        animate="visible"
        variants={containerVariants}
        className="w-full max-w-md relative z-10"
      >
        {/* Animated status bar */}
        <motion.div
          variants={itemVariants}
          className="mb-6 flex justify-center gap-2"
        >
          <div className="flex items-center gap-1 px-3 py-1 bg-white/5 backdrop-blur-sm rounded-full border border-white/10">
            <Shield className="w-3 h-3 text-green-400" />
            <span className="text-xs text-gray-300">{t('common.secureConnection')}</span>
          </div>
          <div className="flex items-center gap-1 px-3 py-1 bg-white/5 backdrop-blur-sm rounded-full border border-white/10">
            <Star className="w-3 h-3 text-yellow-400" />
            <span className="text-xs text-gray-300">{t('common.enterpriseGrade')}</span>
          </div>
        </motion.div>

        {/* Logo with advanced animation */}
        <motion.div
          variants={itemVariants}
          className="flex items-center justify-center gap-3 mb-8"
        >
          <div className="relative group">
            <div className="w-16 h-16 bg-gradient-to-br from-pink-500 via-purple-500 to-blue-500 rounded-2xl flex items-center justify-center transform rotate-3 group-hover:rotate-6 transition-all duration-500 shadow-2xl">
              <Zap className="w-8 h-8 text-white animate-pulse" />
            </div>
            <motion.div
              animate={{
                scale: [1, 1.2, 1],
                opacity: [0.5, 0.8, 0.5]
              }}
              transition={{
                duration: 3,
                repeat: Infinity,
                ease: "easeInOut"
              }}
              className="absolute inset-0 bg-gradient-to-br from-pink-500 to-blue-500 rounded-2xl blur-2xl -z-10"
            />
            {/* Orbiting rings */}
            <div className="absolute -inset-2 border border-pink-500/20 rounded-full animate-spin-slow" />
            <div className="absolute -inset-3 border border-blue-500/10 rounded-full animate-spin-slower" />
          </div>
          <div className="relative">
            <span className="text-5xl font-black bg-gradient-to-r from-pink-400 via-purple-400 to-blue-400 bg-clip-text text-transparent">
              Velocity
            </span>
            <div className="absolute -bottom-2 left-0 right-0 h-0.5 bg-gradient-to-r from-pink-500 to-blue-500 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-500" />
          </div>
        </motion.div>

        {/* Welcome text with typewriter */}
        <motion.div
          variants={itemVariants}
          className="text-center mb-6"
        >
          <div className="text-2xl font-light text-gray-300">
            <Typewriter
              options={{
                strings: t('signInPage.welcomeMessages'),
                autoStart: true,
                loop: true,
                delay: 50,
                deleteSpeed: 30,
                wrapperClassName: "bg-gradient-to-r from-pink-400 to-blue-400 bg-clip-text text-transparent font-bold"
              }}
            />
          </div>
        </motion.div>

        {/* Form Card with 3D tilt effect */}
        <motion.div
          ref={cardRef}
          variants={itemVariants}
          style={{
            transform: `perspective(1000px) rotateX(${mousePosition.y * 10}deg) rotateY(${mousePosition.x * 10}deg)`
          }}
          className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-3xl p-8 shadow-2xl relative overflow-hidden transition-transform duration-200"
        >
          {/* Animated gradient background inside card */}
          <div className="absolute inset-0 bg-gradient-to-r from-pink-500/0 via-purple-500/5 to-blue-500/0 animate-gradient-x" />

          {/* Glowing orbs inside card */}
          <div className="absolute -top-20 -right-20 w-40 h-40 bg-pink-500 rounded-full mix-blend-multiply filter blur-2xl opacity-20 animate-pulse" />
          <div className="absolute -bottom-20 -left-20 w-40 h-40 bg-blue-500 rounded-full mix-blend-multiply filter blur-2xl opacity-20 animate-pulse animation-delay-2000" />

          {/* Animated border */}
          <div className="absolute inset-0 rounded-3xl p-[1px] bg-gradient-to-r from-pink-500 via-purple-500 to-blue-500 opacity-0 group-hover:opacity-100 transition-opacity duration-500">
            <div className="absolute inset-0 rounded-3xl bg-gray-950/90" />
          </div>

          <div className="relative">
            <motion.div variants={itemVariants} className="text-center mb-8">
              <h2 className="text-3xl font-bold mb-2 flex items-center justify-center gap-2">
                <Sparkles className="w-6 h-6 text-yellow-400 animate-pulse" />
                {t('signInPage.title')}
                <Sparkles className="w-6 h-6 text-yellow-400 animate-pulse animation-delay-1000" />
              </h2>
              <p className="text-gray-400">
                {t('signInPage.subtitle')}
              </p>
            </motion.div>

            <form onSubmit={handleSubmit} className="space-y-5">
              <motion.div variants={itemVariants}>
                <label className="block text-sm font-medium mb-2 text-gray-300 flex items-center gap-2">
                  <Mail className="w-4 h-4 text-pink-400" />
                  Email Address
                </label>
                <div className="relative group">
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    placeholder="you@example.com"
                    className="w-full pl-4 pr-4 py-4 bg-white/5 border border-white/10 rounded-xl focus:border-pink-500 focus:outline-none transition-all duration-300 text-white placeholder-gray-600 hover:bg-white/10"
                    required
                  />
                  <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-pink-500 to-blue-500 opacity-0 group-hover:opacity-20 blur-xl transition-opacity -z-10" />
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-pink-500 to-blue-500 transform scale-x-0 group-focus-within:scale-x-100 transition-transform duration-500 origin-left" />
                </div>
              </motion.div>

              <motion.div variants={itemVariants}>
                <label className="block text-sm font-medium mb-2 text-gray-300 flex items-center gap-2">
                  <Lock className="w-4 h-4 text-pink-400" />
                  Password
                </label>
                <div className="relative group">
                  <input
                    type={showPassword ? "text" : "password"}
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    placeholder="••••••••"
                    className="w-full pl-4 pr-12 py-4 bg-white/5 border border-white/10 rounded-xl focus:border-pink-500 focus:outline-none transition-all duration-300 text-white placeholder-gray-600 hover:bg-white/10"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-pink-400 transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-pink-500 to-blue-500 transform scale-x-0 group-focus-within:scale-x-100 transition-transform duration-500 origin-left" />
                </div>
              </motion.div>

              <motion.div
                variants={itemVariants}
                className="flex items-center justify-between text-sm"
              >
                <label className="flex items-center gap-2 cursor-pointer group">
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={rememberMe}
                      onChange={(e) => setRememberMe(e.target.checked)}
                      className="w-4 h-4 rounded border-gray-600 bg-white/5 text-pink-500 focus:ring-pink-500 focus:ring-offset-0 focus:ring-1 opacity-0 absolute"
                    />
                    <div className={`w-4 h-4 rounded border ${rememberMe ? 'bg-pink-500 border-pink-500' : 'border-gray-600 bg-white/5'} flex items-center justify-center transition-all duration-300`}>
                      {rememberMe && (
                        <motion.svg
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          className="w-3 h-3 text-white"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="3"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        >
                          <polyline points="20 6 9 17 4 12" />
                        </motion.svg>
                      )}
                    </div>
                  </div>
                  <span className="text-gray-400 group-hover:text-gray-300 transition-colors">
                    {t('common.rememberMe')}
                  </span>
                </label>
                <a
                  href="#"
                  className="text-pink-400 hover:text-pink-300 transition-colors text-sm relative group"
                >
                  Forgot password?
                  <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-pink-400 group-hover:w-full transition-all duration-300" />
                </a>
              </motion.div>

              {/* Error Message */}
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 flex items-center gap-2"
                >
                  <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
                  <p className="text-red-400 text-sm">{error}</p>
                </motion.div>
              )}

              {/* Success Message */}
              {successMessage && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-green-500/10 border border-green-500/30 rounded-lg p-3 flex items-center gap-2"
                >
                  <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
                  <p className="text-green-400 text-sm">{successMessage}</p>
                </motion.div>
              )}

              <motion.button
                variants={itemVariants}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                type="submit"
                disabled={isLoading}
                className="w-full py-4 bg-gradient-to-r from-pink-500 via-purple-500 to-blue-500 rounded-xl font-semibold relative overflow-hidden group disabled:opacity-70 disabled:cursor-not-allowed"
              >
                <span className="relative z-10 flex items-center justify-center gap-2">
                  {isLoading ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      {t('signInPage.signingIn')}
                    </>
                  ) : (
                    <>
                      Sign In
                      <ArrowRight className="w-4 h-4 group-hover:translate-x-2 transition-transform" />
                    </>
                  )}
                </span>
                <div className="absolute inset-0 bg-gradient-to-r from-pink-600 via-purple-600 to-blue-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                <div className="absolute inset-0 bg-white/20 transform -skew-x-12 -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />
              </motion.button>
            </form>

            <motion.p
              variants={itemVariants}
              className="text-center text-gray-400 mt-8 text-sm"
            >
              New to Velocity?{' '}
              <Link
                to="/signup"
                className="text-pink-400 hover:text-pink-300 transition-colors font-semibold relative group"
              >
                Create Account
                <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-pink-400 group-hover:w-full transition-all duration-300" />
              </Link>
            </motion.p>
          </div>
        </motion.div>

        {/* Trust indicators */}
        <motion.div
          variants={itemVariants}
          className="mt-8 grid grid-cols-3 gap-4 text-center text-xs text-gray-500"
        >
          <div className="flex flex-col items-center gap-1">
            <Shield className="w-4 h-4 text-green-400" />
            <span>{t('common.encryption')}</span>
          </div>
          <div className="flex flex-col items-center gap-1">
            <div className="w-4 h-4 rounded-full bg-green-400 animate-pulse" />
            <span>{t('common.uptime')}</span>
          </div>
          <div className="flex flex-col items-center gap-1">
            <Star className="w-4 h-4 text-yellow-400" />
            <span>{t('common.support')}</span>
          </div>
        </motion.div>
      </motion.div>

      <style>{`
        @keyframes blob {
          0% { transform: translate(0px, 0px) scale(1); }
          33% { transform: translate(30px, -50px) scale(1.1); }
          66% { transform: translate(-20px, 20px) scale(0.9); }
          100% { transform: translate(0px, 0px) scale(1); }
        }
        .animate-blob {
          animation: blob 7s infinite;
        }
        .animation-delay-2000 {
          animation-delay: 2s;
        }
        .animation-delay-4000 {
          animation-delay: 4s;
        }
        .animation-delay-1000 {
          animation-delay: 1s;
        }
        @keyframes slide {
          from { transform: translateX(0); }
          to { transform: translateX(100%); }
        }
        @keyframes gradient-xy {
          0%, 100% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
        }
        .animate-gradient-xy {
          background-size: 400% 400%;
          animation: gradient-xy 15s ease infinite;
        }
        @keyframes spin-slow {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .animate-spin-slow {
          animation: spin-slow 8s linear infinite;
        }
        .animate-spin-slower {
          animation: spin-slow 12s linear infinite;
        }
        .bg-radial-gradient {
          background: radial-gradient(circle at center, transparent 0%, rgba(3, 3, 15, 0.8) 100%);
        }
      `}</style>
    </div>
  );
}