import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function Profile() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  // Mask phone for display: +234 801 *** **78
  const maskedPhone = user?.phone
    ? `+${user.phone.slice(0, 6)} *** **${user.phone.slice(-2)}`
    : '+234 ***'

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900">Profile</h2>

      {/* Profile Card */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 text-center">
        <div className="w-20 h-20 bg-emerald-100 rounded-full mx-auto flex items-center justify-center text-3xl">
          👤
        </div>
        <p className="font-semibold text-gray-900 mt-3">
          {user?.display_name || 'FinPad User'}
        </p>
        <p className="text-sm text-gray-500">{maskedPhone}</p>
      </div>

      {/* Stats */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h3 className="font-semibold text-gray-900 mb-4">Your Stats</h3>
        <div className="space-y-3">
          <div className="flex justify-between">
            <span className="text-gray-500 text-sm">Current Streak</span>
            <span className="font-medium">{user?.current_streak || 0} days 🔥</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500 text-sm">Level</span>
            <span className="font-medium text-emerald-600">{user?.level || 'Beginner Saver'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500 text-sm">Badges Earned</span>
            <span className="font-medium">0</span>
          </div>
        </div>
      </div>

      {/* WhatsApp Status */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h3 className="font-semibold text-gray-900 mb-2">WhatsApp</h3>
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-500">Connection Status</span>
          <span className={`text-sm font-medium ${user?.whatsapp_linked ? 'text-emerald-600' : 'text-red-500'}`}>
            {user?.whatsapp_linked ? 'Linked ✓' : 'Not Linked'}
          </span>
        </div>
      </div>

      {/* Settings */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h3 className="font-semibold text-gray-900 mb-4">Settings</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Currency</span>
            <span className="text-sm font-medium">{user?.currency || 'NGN'} (₦)</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Daily Reminders</span>
            <span className="text-sm font-medium text-emerald-600">
              {user?.notification_enabled ? `On - ${user.daily_reminder_time || '8:00 PM'}` : 'Off'}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Notifications</span>
            <span className={`text-sm font-medium ${user?.notification_enabled ? 'text-emerald-600' : 'text-red-500'}`}>
              {user?.notification_enabled ? 'Enabled' : 'Disabled'}
            </span>
          </div>
        </div>
      </div>

      {/* Logout */}
      <button
        onClick={handleLogout}
        className="w-full py-3 rounded-xl border border-red-200 text-red-600 font-medium hover:bg-red-50 transition-colors"
      >
        Logout
      </button>
    </div>
  )
}
