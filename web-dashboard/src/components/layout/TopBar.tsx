import { Search, Bell, User, LogOut } from 'lucide-react'
import { useAuthStore } from '../../store/authStore'

export default function TopBar() {
  const { user, logout } = useAuthStore()

  return (
    <header className="h-16 glass-card m-4 mb-0 rounded-b-none border-b flex items-center justify-between px-6">
      {/* Search bar */}
      <div className="flex-1 max-w-md">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search files, tags, or categories..."
            className="w-full bg-space-800 border border-white/10 rounded-lg pl-10 pr-4 py-2
                     focus:border-neon-cyan focus:outline-none focus:ring-2 focus:ring-neon-cyan/20
                     transition-all duration-200"
          />
        </div>
      </div>

      {/* Right section */}
      <div className="flex items-center gap-4">
        {/* Notifications */}
        <button className="relative p-2 hover:bg-white/5 rounded-lg transition-colors">
          <Bell className="w-5 h-5 text-gray-400" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-neon-magenta rounded-full" />
        </button>

        {/* User menu */}
        <div className="flex items-center gap-3 pl-4 border-l border-white/10">
          <div className="text-right">
            <p className="text-sm font-semibold">{user?.full_name || user?.username}</p>
            <p className="text-xs text-neon-cyan capitalize">{user?.subscription_tier} Plan</p>
          </div>

          <div className="relative group">
            <button className="w-10 h-10 bg-gradient-to-br from-neon-cyan to-neon-magenta rounded-full
                             flex items-center justify-center font-bold">
              {user?.username?.[0]?.toUpperCase() || 'U'}
            </button>

            {/* Dropdown */}
            <div className="absolute right-0 mt-2 w-48 glass-card rounded-lg shadow-xl opacity-0
                          invisible group-hover:opacity-100 group-hover:visible transition-all duration-200
                          z-50">
              <div className="p-2">
                <button className="w-full flex items-center gap-3 px-3 py-2 rounded hover:bg-white/5
                                 transition-colors text-left">
                  <User className="w-4 h-4" />
                  <span className="text-sm">Profile</span>
                </button>
                <button
                  onClick={logout}
                  className="w-full flex items-center gap-3 px-3 py-2 rounded hover:bg-white/5
                           transition-colors text-left text-red-400"
                >
                  <LogOut className="w-4 h-4" />
                  <span className="text-sm">Logout</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}
