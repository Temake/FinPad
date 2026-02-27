export default function Education() {
  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900">Financial Tips 📚</h2>

      {/* Daily Tip */}
      <div className="bg-gradient-to-r from-emerald-500 to-teal-600 text-white rounded-2xl p-6">
        <p className="text-xs uppercase tracking-wide opacity-80">💡 Tip of the Day</p>
        <p className="text-lg font-medium mt-2">
          The 50/30/20 rule: Spend 50% on needs, 30% on wants, and save 20% of your income.
        </p>
        <p className="text-xs mt-3 opacity-70">Tip #1 • Budgeting Basics</p>
      </div>

      {/* Categories */}
      <div className="grid grid-cols-2 gap-4">
        {[
          { icon: '🏦', title: 'Savings', count: 25 },
          { icon: '📈', title: 'Investing', count: 18 },
          { icon: '💳', title: 'Budgeting', count: 30 },
          { icon: '🚫', title: 'Debt Management', count: 15 },
        ].map((cat) => (
          <div
            key={cat.title}
            className="bg-white rounded-xl p-4 shadow-sm border border-gray-100 cursor-pointer hover:border-emerald-200 transition-colors"
          >
            <span className="text-2xl">{cat.icon}</span>
            <p className="font-medium text-gray-900 mt-2">{cat.title}</p>
            <p className="text-xs text-gray-500">{cat.count} tips</p>
          </div>
        ))}
      </div>
    </div>
  )
}
