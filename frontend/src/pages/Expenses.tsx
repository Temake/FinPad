export default function Expenses() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900">Expenses</h2>
        <button className="bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-emerald-700 transition-colors">
          + Add Expense
        </button>
      </div>

      {/* Filters Placeholder */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {['All', 'Today', 'This Week', 'This Month'].map((filter) => (
          <button
            key={filter}
            className="px-3 py-1 rounded-full text-sm border border-gray-200 text-gray-600 hover:bg-emerald-50 hover:border-emerald-200 hover:text-emerald-700 whitespace-nowrap transition-colors"
          >
            {filter}
          </button>
        ))}
      </div>

      {/* Expense List Placeholder */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <p className="text-gray-500 text-sm text-center py-12">
          No expenses yet. Tap "Add Expense" to get started! 💰
        </p>
      </div>
    </div>
  )
}
