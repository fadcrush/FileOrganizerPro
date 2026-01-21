import { HardDrive, Files, Copy, TrendingUp, Clock, Zap } from 'lucide-react'
import { motion } from 'framer-motion'

const stats = [
  {
    label: 'Total Files',
    value: '5,420',
    change: '+12%',
    icon: Files,
    color: 'cyan'
  },
  {
    label: 'Storage Used',
    value: '45.2 GB',
    change: '+2.5 GB',
    icon: HardDrive,
    color: 'magenta'
  },
  {
    label: 'Duplicates Found',
    value: '340',
    change: '2.8 GB saved',
    icon: Copy,
    color: 'green'
  },
  {
    label: 'Organization Jobs',
    value: '24',
    change: '+8 this week',
    icon: Zap,
    color: 'cyan'
  },
]

const recentFiles = [
  { name: 'vacation_photo.jpg', category: 'Images', size: '2.4 MB', time: '2 min ago' },
  { name: 'project_proposal.pdf', category: 'Documents', size: '856 KB', time: '15 min ago' },
  { name: 'presentation.pptx', category: 'Presentations', size: '12.5 MB', time: '1 hour ago' },
  { name: 'video_edit.mp4', category: 'Videos', size: '245 MB', time: '2 hours ago' },
]

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
}

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 }
}

export default function Dashboard() {
  return (
    <div className="space-y-6">
      {/* Welcome header */}
      <div>
        <h1 className="text-3xl font-bold glow-cyan mb-2">
          Welcome back! 👋
        </h1>
        <p className="text-gray-400">
          Here's what's happening with your files today
        </p>
      </div>

      {/* Stats grid */}
      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
      >
        {stats.map((stat, index) => {
          const Icon = stat.icon
          const colorClass = stat.color === 'cyan' ? 'neon-cyan' : stat.color === 'magenta' ? 'neon-magenta' : 'neon-green'

          return (
            <motion.div
              key={stat.label}
              variants={item}
              className="glass-card p-6 rounded-xl hover:border-neon-cyan/50 transition-all duration-300 cursor-pointer group"
            >
              <div className="flex items-start justify-between mb-4">
                <div className={`p-3 rounded-lg bg-${stat.color === 'cyan' ? 'neon-cyan' : stat.color === 'magenta' ? 'neon-magenta' : 'neon-green'}/20`}>
                  <Icon className={`w-6 h-6 text-${colorClass}`} />
                </div>
                <span className="text-sm text-green-400 font-semibold">
                  {stat.change}
                </span>
              </div>
              <h3 className="text-2xl font-bold mb-1 group-hover:text-neon-cyan transition-colors">
                {stat.value}
              </h3>
              <p className="text-gray-400 text-sm">{stat.label}</p>
            </motion.div>
          )
        })}
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Files */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
          className="lg:col-span-2 glass-card p-6 rounded-xl"
        >
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold flex items-center gap-2">
              <Clock className="w-5 h-5 text-neon-cyan" />
              Recent Files
            </h2>
            <button className="text-sm text-neon-cyan hover:text-neon-magenta transition-colors">
              View All →
            </button>
          </div>

          <div className="space-y-3">
            {recentFiles.map((file, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.5 + index * 0.1 }}
                className="flex items-center justify-between p-4 rounded-lg bg-space-800/50
                         hover:bg-space-800 transition-all duration-200 cursor-pointer group"
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-lg bg-neon-cyan/20 flex items-center justify-center
                                group-hover:bg-neon-cyan/30 transition-colors">
                    <Files className="w-5 h-5 text-neon-cyan" />
                  </div>
                  <div>
                    <p className="font-semibold group-hover:text-neon-cyan transition-colors">
                      {file.name}
                    </p>
                    <p className="text-sm text-gray-400">{file.category} • {file.size}</p>
                  </div>
                </div>
                <span className="text-sm text-gray-500">{file.time}</span>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Quick Actions */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
          className="glass-card p-6 rounded-xl"
        >
          <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
            <Zap className="w-5 h-5 text-neon-green" />
            Quick Actions
          </h2>

          <div className="space-y-3">
            <button className="w-full btn-primary text-left flex items-center gap-3">
              <div className="w-10 h-10 bg-space-950/50 rounded-lg flex items-center justify-center">
                📁
              </div>
              <div>
                <p className="font-bold">Organize Files</p>
                <p className="text-xs opacity-80">Start new job</p>
              </div>
            </button>

            <button className="w-full btn-secondary text-left flex items-center gap-3">
              <div className="w-10 h-10 bg-neon-magenta/10 rounded-lg flex items-center justify-center">
                ♻️
              </div>
              <div>
                <p className="font-semibold">Review Duplicates</p>
                <p className="text-xs text-gray-400">Free up 2.8 GB</p>
              </div>
            </button>

            <button className="w-full btn-secondary text-left flex items-center gap-3">
              <div className="w-10 h-10 bg-neon-green/10 rounded-lg flex items-center justify-center">
                📤
              </div>
              <div>
                <p className="font-semibold">Upload Files</p>
                <p className="text-xs text-gray-400">Drag & drop or browse</p>
              </div>
            </button>
          </div>

          {/* Storage warning */}
          <div className="mt-6 p-4 bg-amber-500/10 border border-amber-500/30 rounded-lg">
            <p className="text-sm text-amber-400 font-semibold mb-1">
              ⚠️ Storage Notice
            </p>
            <p className="text-xs text-gray-400">
              You're using 45% of your storage. Consider upgrading to Pro for 100GB.
            </p>
            <button className="mt-2 text-xs text-neon-cyan hover:text-neon-magenta transition-colors font-semibold">
              Upgrade Now →
            </button>
          </div>
        </motion.div>
      </div>

      {/* Activity Timeline */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="glass-card p-6 rounded-xl"
      >
        <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-neon-magenta" />
          Recent Activity
        </h2>

        <div className="space-y-4">
          <div className="flex items-center gap-4 p-3 rounded-lg bg-space-800/30">
            <div className="w-2 h-2 rounded-full bg-neon-green animate-pulse" />
            <p className="text-sm">
              <span className="text-neon-cyan font-semibold">Organization job</span> completed •
              <span className="text-gray-400"> 450 files processed</span>
            </p>
            <span className="ml-auto text-xs text-gray-500">5 min ago</span>
          </div>

          <div className="flex items-center gap-4 p-3 rounded-lg bg-space-800/30">
            <div className="w-2 h-2 rounded-full bg-neon-cyan" />
            <p className="text-sm">
              <span className="text-neon-magenta font-semibold">25 duplicates</span> detected •
              <span className="text-gray-400"> 340 MB potential savings</span>
            </p>
            <span className="ml-auto text-xs text-gray-500">1 hour ago</span>
          </div>

          <div className="flex items-center gap-4 p-3 rounded-lg bg-space-800/30">
            <div className="w-2 h-2 rounded-full bg-neon-magenta" />
            <p className="text-sm">
              <span className="text-neon-green font-semibold">Uploaded</span> 15 new files •
              <span className="text-gray-400"> 124 MB added</span>
            </p>
            <span className="ml-auto text-xs text-gray-500">3 hours ago</span>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
