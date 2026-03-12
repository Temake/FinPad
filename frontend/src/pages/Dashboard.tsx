import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { expensesApi } from '../services/api'
import type { Expense, ExpenseSummary } from '../types/expense'

export default function Dashboard() {
  const { user } = useAuth()
  const [todaySummary, setTodaySummary] = useState<ExpenseSummary | null>(null)
  const [monthSummary, setMonthSummary] = useState<ExpenseSummary | null>(null)
  const [recentExpenses, setRecentExpenses] = useState<Expense[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [todayRes, monthRes, recentRes] = await Promise.all([
          expensesApi.summary('daily'),
          expensesApi.summary('monthly'),
          expensesApi.list({ limit: 5 }),
        ])
        setTodaySummary(todayRes.data)
        setMonthSummary(monthRes.data)
        setRecentExpenses(recentRes.data)
      } catch (err) {
        console.error('Failed to fetch dashboard data:', err)
      } finally {
        setIsLoading(false)
      }
    }
    fetchData()
  }, [])

  const greeting = () => {
    const hour = new Date().getHours()
    if (hour < 12) return 'Good morning'
    if (hour < 17) return 'Good afternoon'
    return 'Good evening'
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-NG', {
      style: 'currency',
      currency: 'NGN',
      minimumFractionDigits: 0,
    }).format(amount)
  }

  // Calculate top spending category
  const topCategory = monthSummary?.by_category
    ? Object.entries(monthSummary.by_category).sort(([, a], [, b]) => b - a)[0]
    : null

  return (
    <div className="space-y-6 pb-20">
      {/* Welcome */}
      <div className="bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-2xl p-6">
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
          <p className="text-2xl font-bold text-gray-900 mt-1">
            {isLoading ? '...' : formatCurrency(todaySummary?.total || 0)}
          </p>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <p className="text-xs text-gray-500">This Month</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">
            {isLoading ? '...' : formatCurrency(monthSummary?.total || 0)}
          </p>
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

      {/* Top Category */}
      {topCategory && (
        <div className="bg-amber-50 rounded-xl p-4 border border-amber-100">
          <p className="text-xs text-amber-700">🏆 Top spending category</p>
          <p className="text-lg font-semibold text-amber-900 mt-1">
            {topCategory[0]}: {formatCurrency(topCategory[1])}
          </p>
        </div>
      )}

      {/* Recent Expenses */}
      <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-900">Recent Expenses</h3>
          <Link to="/expenses" className="text-sm text-emerald-600 hover:underline">
            See all
          </Link>
        </div>

        {isLoading ? (
          <p className="text-gray-500 text-sm text-center py-6">Loading...</p>
        ) : recentExpenses.length === 0 ? (
          <div className="text-center py-6">
            <p className="text-gray-500 text-sm">No expenses logged yet. Start tracking! 📝</p>
            <Link
              to="/expenses"
              className="inline-block mt-3 text-sm text-emerald-600 font-medium hover:underline"
            >
              Add your first expense →
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {recentExpenses.map((expense) => (
              <div
                key={expense.id}
                className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0"
              >
                <div className="flex items-center gap-3">
                  <span className="text-lg">{expense.category_icon || '📦'}</span>
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {expense.description || expense.category_name || 'Expense'}
                    </p>
                    <p className="text-xs text-gray-500">{expense.category_name || 'Uncategorized'}</p>
                  </div>
                </div>
                <p className="text-sm font-semibold text-gray-900">
                  {formatCurrency(expense.amount)}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 gap-4">
        <Link
          to="/expenses"
          className="bg-emerald-600 text-white rounded-xl p-4 text-center font-medium hover:bg-emerald-700 transition-colors"
        >
          + Add Expense
        </Link>
        <Link
          to="/education"
          className="bg-white text-emerald-600 rounded-xl p-4 text-center font-medium border border-emerald-200 hover:bg-emerald-50 transition-colors"
        >
          📚 Learn
        </Link>
      </div>
    </div>
  )
}
