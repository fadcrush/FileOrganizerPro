import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Rocket, Mail, Lock, Eye, EyeOff } from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import toast from 'react-hot-toast'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const navigate = useNavigate()
  const login = useAuthStore((state) => state.login)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    // Simulate API call
    setTimeout(() => {
      // Demo login - accept any credentials
      login(
        {
          id: '123',
          email,
          username: email.split('@')[0],
          full_name: 'John Doe',
          subscription_tier: 'pro',
        },
        'demo-token-123'
      )

      toast.success('Welcome back!')
      navigate('/')
      setIsLoading(false)
    }, 1000)
  }

  return (
    <div className="min-h-screen bg-space-950 flex items-center justify-center p-4 relative overflow-hidden">
      {/* Animated background */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-neon-cyan/10 rounded-full blur-3xl animate-pulse-slow" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-neon-magenta/10 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }} />
        <div className="absolute top-1/2 left-1/2 w-96 h-96 bg-neon-green/5 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '2s' }} />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-4">
            <Rocket className="w-12 h-12 text-neon-cyan" />
            <h1 className="text-4xl font-bold glow-cyan">FileOrganizer Pro</h1>
          </div>
          <p className="text-gray-400">Sign in to access your dashboard</p>
        </div>

        {/* Login form */}
        <div className="glass-card p-8 rounded-2xl">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Email field */}
            <div>
              <label className="block text-sm font-semibold mb-2 text-gray-300">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  required
                  className="w-full bg-space-800 border border-white/10 rounded-lg pl-10 pr-4 py-3
                           focus:border-neon-cyan focus:outline-none focus:ring-2 focus:ring-neon-cyan/20
                           transition-all duration-200"
                />
              </div>
            </div>

            {/* Password field */}
            <div>
              <label className="block text-sm font-semibold mb-2 text-gray-300">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full bg-space-800 border border-white/10 rounded-lg pl-10 pr-12 py-3
                           focus:border-neon-cyan focus:outline-none focus:ring-2 focus:ring-neon-cyan/20
                           transition-all duration-200"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            {/* Remember me & Forgot password */}
            <div className="flex items-center justify-between text-sm">
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" className="w-4 h-4 rounded border-gray-600 bg-space-800 text-neon-cyan
                                                 focus:ring-2 focus:ring-neon-cyan/20" />
                <span className="text-gray-400">Remember me</span>
              </label>
              <a href="#" className="text-neon-cyan hover:text-neon-magenta transition-colors">
                Forgot password?
              </a>
            </div>

            {/* Submit button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full btn-primary justify-center disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <span className="flex items-center gap-2">
                  <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                  Signing in...
                </span>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          {/* Demo info */}
          <div className="mt-6 p-4 bg-neon-cyan/10 border border-neon-cyan/30 rounded-lg">
            <p className="text-sm text-neon-cyan font-semibold mb-1">
              🎭 Demo Mode
            </p>
            <p className="text-xs text-gray-400">
              Enter any email and password to try the dashboard. No real authentication required.
            </p>
          </div>

          {/* Sign up link */}
          <p className="mt-6 text-center text-sm text-gray-400">
            Don't have an account?{' '}
            <a href="#" className="text-neon-cyan hover:text-neon-magenta transition-colors font-semibold">
              Sign up for free
            </a>
          </p>
        </div>

        {/* Features */}
        <div className="mt-8 grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-2xl font-bold text-neon-cyan">100GB</p>
            <p className="text-xs text-gray-500">Cloud Storage</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-neon-magenta">AI-Powered</p>
            <p className="text-xs text-gray-500">Smart Organization</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-neon-green">99.9%</p>
            <p className="text-xs text-gray-500">Uptime</p>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
