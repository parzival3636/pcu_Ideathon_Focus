import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { 
  Mail, 
  Lock, 
  User,
  Sparkles,
  Eye,
  EyeOff,
  ArrowRight,
  Shield,
  Star,
  Rocket,
  AlertCircle
} from 'lucide-react';
import { motion } from 'framer-motion';
import Typewriter from 'typewriter-effect';
import { authenticationAPI } from '../services/api';

export default function SignUp() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [agreeTerms, setAgreeTerms] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    // Validation
    if (!formData.name.trim()) {
      setError('Please enter your name');
      return;
    }
    if (!formData.email.trim()) {
      setError('Please enter your email');
      return;
    }
    if (!formData.password || formData.password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }
    if (!agreeTerms) {
      setError('Please agree to the terms and conditions');
      return;
    }

    setIsLoading(true);
    
    try {
      await authenticationAPI.signup(formData);
      // On success, navigate to signin
      navigate('/signin', { 
        state: { message: 'Account created successfully! Please sign in.' }
      });
    } catch (err) {
      console.error('Signup error:', err);
      setError(
        err.response?.data?.error || 
        err.response?.data?.message ||
        'Failed to create account. Please try again.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.3
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-950 to-slate-950 text-white relative overflow-hidden">
      {/* Animated gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-purple-900/20 via-pink-900/20 to-blue-900/20 animate-gradient-xy" />
      
      {/* Floating orbs */}
      <div className="absolute top-20 left-20 w-96 h-96 bg-purple-600 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob" />
      <div className="absolute top-40 right-20 w-96 h-96 bg-pink-600 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000" />
      <div className="absolute bottom-20 left-1/2 w-96 h-96 bg-blue-600 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000" />

      {/* Form UI */}
      <div className="absolute inset-0 flex items-center justify-center z-20 p-6">
        <motion.div
          initial="hidden"
          animate="visible"
          variants={containerVariants}
          className="w-full max-w-md"
        >
          {/* Logo */}
          <motion.div
            variants={itemVariants}
            className="flex flex-col items-center justify-center mb-8"
          >
            <div className="relative group mb-2">
              <div className="flex items-center justify-center gap-1">
                <Rocket className="w-10 h-10 text-transparent bg-gradient-to-r from-pink-400 to-blue-400 bg-clip-text" strokeWidth={1.5} />
                <span className="text-5xl font-black bg-gradient-to-r from-pink-400 via-purple-400 to-blue-400 bg-clip-text text-transparent tracking-tight">
                  V
                </span>
              </div>
              <motion.div 
                className="absolute -bottom-2 left-1/2 transform -translate-x-1/2 w-12 h-0.5 bg-gradient-to-r from-pink-500 to-blue-500"
                animate={{
                  width: ['3rem', '5rem', '3rem'],
                  opacity: [0.5, 1, 0.5]
                }}
                transition={{
                  duration: 3,
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
              />
            </div>
            <span className="text-3xl font-light text-gray-300 tracking-widest">VELOCITY</span>
          </motion.div>

          {/* Welcome text */}
          <motion.div 
            variants={itemVariants}
            className="text-center mb-6"
          >
            <div className="text-2xl font-light text-gray-300">
              <Typewriter
                options={{
                  strings: ['Join the Adventure! 🚀', 'Start Your Journey! 👋', 'Begin Learning Today! ⚡'],
                  autoStart: true,
                  loop: true,
                  delay: 50,
                  deleteSpeed: 30,
                  wrapperClassName: "bg-gradient-to-r from-pink-400 to-blue-400 bg-clip-text text-transparent font-bold"
                }}
              />
            </div>
          </motion.div>

          {/* Sign Up Card */}
          <motion.div
            variants={itemVariants}
            className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-8 shadow-2xl relative overflow-hidden"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-pink-500/0 via-purple-500/5 to-blue-500/0" />
            
            <div className="relative">
              <h2 className="text-2xl font-bold text-center mb-2 flex items-center justify-center gap-2">
                <Sparkles className="w-5 h-5 text-pink-400" />
                Create Account
                <Sparkles className="w-5 h-5 text-blue-400" />
              </h2>
              <p className="text-gray-300 text-center text-sm mb-8">
                Start your learning journey today!
              </p>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-300">
                    Full Name
                  </label>
                  <div className="relative group">
                    <User className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      placeholder="John Doe"
                      className="w-full pl-12 pr-4 py-3.5 bg-white/10 border border-white/20 rounded-xl focus:border-pink-500 focus:outline-none transition-all text-white placeholder-gray-500"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-300">
                    Email
                  </label>
                  <div className="relative group">
                    <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      placeholder="you@example.com"
                      className="w-full pl-12 pr-4 py-3.5 bg-white/10 border border-white/20 rounded-xl focus:border-pink-500 focus:outline-none transition-all text-white placeholder-gray-500"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-300">
                    Password
                  </label>
                  <div className="relative group">
                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                      type={showPassword ? "text" : "password"}
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      placeholder="••••••••"
                      className="w-full pl-12 pr-12 py-3.5 bg-white/10 border border-white/20 rounded-xl focus:border-pink-500 focus:outline-none transition-all text-white placeholder-gray-500"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-pink-400"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="terms"
                    checked={agreeTerms}
                    onChange={(e) => setAgreeTerms(e.target.checked)}
                    className="w-4 h-4 rounded border-gray-600 bg-white/10 text-pink-500"
                  />
                  <label htmlFor="terms" className="text-sm text-gray-300">
                    I agree to the{' '}
                    <a href="#" className="text-pink-400 hover:text-pink-300">Terms</a>
                  </label>
                </div>

                {/* Error Message */}
                {error && (
                  <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 flex items-center gap-2">
                    <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
                    <p className="text-red-400 text-sm">{error}</p>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={isLoading || !agreeTerms}
                  className="w-full py-3.5 bg-gradient-to-r from-pink-500 to-blue-500 rounded-xl font-semibold hover:shadow-lg hover:shadow-pink-500/25 transition-all disabled:opacity-50"
                >
                  <span className="flex items-center justify-center gap-2">
                    {isLoading ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        Creating Account...
                      </>
                    ) : (
                      <>
                        Create Account
                        <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </span>
                </button>
              </form>

              <p className="text-center text-gray-300 mt-6 text-sm">
                Already have an account?{' '}
                <Link to="/signin" className="text-pink-400 hover:text-pink-300 font-medium">
                  Sign In
                </Link>
              </p>
            </div>
          </motion.div>

          {/* Trust indicators */}
          <motion.div 
            variants={itemVariants}
            className="mt-6 flex justify-center gap-4 text-xs text-gray-400"
          >
            <span className="flex items-center gap-1">
              <Shield className="w-3 h-3 text-green-400" />
              Secure
            </span>
            <span>•</span>
            <span className="flex items-center gap-1">
              <Star className="w-3 h-3 text-yellow-400" />
              Free Forever
            </span>
          </motion.div>
        </motion.div>
      </div>

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
        @keyframes gradient-xy {
          0%, 100% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
        }
        .animate-gradient-xy {
          background-size: 400% 400%;
          animation: gradient-xy 15s ease infinite;
        }
      `}</style>
    </div>
  );
}
