import { useAuth } from '../hooks/useAuth'

export default function Dashboard() {
  const { user } = useAuth()

  const greeting = () => {
    const hour = new Date().getHours()
    if (hour < 12) return 'Good morning'
    if (hour < 17) return 'Good afternoon'
    return 'Good evening'
  }

  return (
    <div className="space-y-6">
      {/* Welcome */}
      <div className="bg-emerald-600 text-white rounded-2xl p-6">
        <p className="text-sm opacity-80">{greeting()} 👋</p>
        <h2 className="text-2xl font-bold mt-1">
          {user?.display_name ? `Hi, ${user.display_name}` : 'Welcome to FinPad'}
        </h2>
        <p className="text-sm mt-2 opacity-90">Track your spending, build better habits.</p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <p className="text-xs text-gray-500">Today's Spending</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">₦0</p>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <p className="text-xs text-gray-500">This Month</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">₦0</p>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <p className="text-xs text-gray-500">Streak 🔥</p>
          <p className="text-2xl font-bold text-emerald-600 mt-1">{user?.current_streak || 0} days</p>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <p className="text-xs text-gray-500">Level</p>
          <p className="text-lg font-bold text-gray-900 mt-1">{user?.level || 'Beginner'}</p>
        </div>
      </div>

      {/* Recent Expenses Placeholder */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h3 className="font-semibold text-gray-900 mb-4">Recent Expenses</h3>
        <p className="text-gray-500 text-sm text-center py-8">
          No expenses logged yet. Start tracking! 📝
        </p>
      </div>
    </div>
  )
}
