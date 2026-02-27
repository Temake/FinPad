import { NavLink, Outlet } from 'react-router-dom'

const navItems = [
  { to: '/', label: 'Dashboard', icon: '📊' },
  { to: '/expenses', label: 'Expenses', icon: '💰' },
  { to: '/education', label: 'Learn', icon: '📚' },
  { to: '/profile', label: 'Profile', icon: '👤' },
]

export default function Layout() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <h1 className="text-xl font-bold text-emerald-600">💵 FinPad</h1>
          <span className="text-sm text-gray-500">Track. Save. Grow.</span>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-6">
        <Outlet />
      </main>

      {/* Bottom Navigation (mobile-first) */}
      <nav className="bg-white border-t border-gray-200 sticky bottom-0">
        <div className="max-w-7xl mx-auto flex justify-around py-2">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex flex-col items-center px-3 py-1 text-xs transition-colors ${
                  isActive
                    ? 'text-emerald-600 font-semibold'
                    : 'text-gray-500 hover:text-gray-700'
                }`
              }
            >
              <span className="text-lg">{item.icon}</span>
              <span>{item.label}</span>
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  )
}
