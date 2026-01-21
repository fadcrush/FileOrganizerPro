import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Files,
  FolderTree,
  Copy,
  BarChart3,
  Settings,
  Rocket
} from 'lucide-react'

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/files', label: 'Files', icon: Files },
  { path: '/organize', label: 'Organize', icon: FolderTree },
  { path: '/duplicates', label: 'Duplicates', icon: Copy },
  { path: '/analytics', label: 'Analytics', icon: BarChart3 },
  { path: '/settings', label: 'Settings', icon: Settings },
]

export default function Sidebar() {
  return (
    <aside className="w-64 glass-card m-4 mr-0 rounded-r-none border-r flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-white/10">
        <div className="flex items-center gap-3">
          <Rocket className="w-8 h-8 text-neon-cyan" />
          <div>
            <h1 className="text-xl font-bold glow-cyan">FileOrganizer</h1>
            <p className="text-xs text-gray-400">Pro v3.0</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {navItems.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                  isActive
                    ? 'bg-neon-cyan/20 text-neon-cyan border border-neon-cyan/30'
                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon className={`w-5 h-5 ${isActive ? 'glow-cyan' : ''}`} />
                  <span className="font-semibold">{item.label}</span>
                </>
              )}
            </NavLink>
          )
        })}
      </nav>

      {/* Storage indicator */}
      <div className="p-4 border-t border-white/10">
        <div className="glass-card p-4 rounded-lg">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm text-gray-400">Storage</span>
            <span className="text-sm font-bold text-neon-cyan">45.2 GB</span>
          </div>
          <div className="h-2 bg-space-800 rounded-full overflow-hidden">
            <div className="h-full bg-gradient-to-r from-neon-cyan to-neon-magenta w-[45%]" />
          </div>
          <p className="text-xs text-gray-500 mt-2">45.2 GB of 100 GB used</p>
        </div>
      </div>
    </aside>
  )
}
