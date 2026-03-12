import { useState, useEffect } from 'react'
import { expensesApi } from '../services/api'
import type { Expense, Category, ExpenseSummary } from '../types/expense'

type FilterPeriod = 'all' | 'today' | 'week' | 'month'

export default function Expenses() {
  const [expenses, setExpenses] = useState<Expense[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [summary, setSummary] = useState<ExpenseSummary | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [filter, setFilter] = useState<FilterPeriod>('month')
  const [showAddModal, setShowAddModal] = useState(false)
  const [editingExpense, setEditingExpense] = useState<Expense | null>(null)

  // Form state
  const [amount, setAmount] = useState('')
  const [description, setDescription] = useState('')
  const [categoryId, setCategoryId] = useState<number | ''>('')
  const [expenseDate, setExpenseDate] = useState(new Date().toISOString().split('T')[0])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')

  // Calculate date range based on filter
  const getDateRange = () => {
    const today = new Date()
    const todayStr = today.toISOString().split('T')[0]

    switch (filter) {
      case 'today':
        return { start_date: todayStr, end_date: todayStr }
      case 'week': {
        const startOfWeek = new Date(today)
        startOfWeek.setDate(today.getDate() - today.getDay())
        return { start_date: startOfWeek.toISOString().split('T')[0], end_date: todayStr }
      }
      case 'month': {
        const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1)
        return { start_date: startOfMonth.toISOString().split('T')[0], end_date: todayStr }
      }
      default:
        return {}
    }
  }

  const fetchData = async () => {
    setIsLoading(true)
    try {
      const [expensesRes, categoriesRes, summaryRes] = await Promise.all([
        expensesApi.list(getDateRange()),
        expensesApi.getCategories(),
        expensesApi.summary(filter === 'today' ? 'daily' : filter === 'week' ? 'weekly' : 'monthly'),
      ])
      setExpenses(expensesRes.data)
      setCategories(categoriesRes.data)
      setSummary(summaryRes.data)
    } catch (err) {
      console.error('Failed to fetch expenses:', err)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [filter])

  const resetForm = () => {
    setAmount('')
    setDescription('')
    setCategoryId('')
    setExpenseDate(new Date().toISOString().split('T')[0])
    setError('')
    setEditingExpense(null)
  }

  const openAddModal = () => {
    resetForm()
    setShowAddModal(true)
  }

  const openEditModal = (expense: Expense) => {
    setEditingExpense(expense)
    setAmount(expense.amount.toString())
    setDescription(expense.description || '')
    setCategoryId(expense.category_id || '')
    setExpenseDate(expense.expense_date)
    setShowAddModal(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    const amountNum = parseFloat(amount)
    if (isNaN(amountNum) || amountNum <= 0) {
      setError('Please enter a valid amount')
      return
    }

    setIsSubmitting(true)
    try {
      const data = {
        amount: amountNum,
        description: description || undefined,
        category_id: categoryId || undefined,
        expense_date: expenseDate,
      }

      if (editingExpense) {
        await expensesApi.update(editingExpense.id, data)
      } else {
        await expensesApi.create(data)
      }

      setShowAddModal(false)
      resetForm()
      fetchData()
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      setError(error.response?.data?.detail || 'Failed to save expense')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this expense?')) return
    try {
      await expensesApi.delete(id)
      fetchData()
    } catch (err) {
      console.error('Failed to delete expense:', err)
    }
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-NG', {
      style: 'currency',
      currency: 'NGN',
      minimumFractionDigits: 0,
    }).format(amount)
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-NG', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    })
  }

  // Group expenses by date
  const groupedExpenses = expenses.reduce((acc, expense) => {
    const date = expense.expense_date
    if (!acc[date]) acc[date] = []
    acc[date].push(expense)
    return acc
  }, {} as Record<string, Expense[]>)

  const filterLabels: Record<FilterPeriod, string> = {
    all: 'All',
    today: 'Today',
    week: 'This Week',
    month: 'This Month',
  }

  return (
    <div className="space-y-4 pb-20">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900">Expenses</h2>
        <button
          onClick={openAddModal}
          className="bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-emerald-700 transition-colors"
        >
          + Add
        </button>
      </div>

      {/* Summary Card */}
      {summary && (
        <div className="bg-gradient-to-r from-emerald-500 to-teal-500 rounded-xl p-4 text-white">
          <p className="text-sm opacity-80">
            {filter === 'today' ? "Today's" : filter === 'week' ? 'This Week' : 'This Month'} Spending
          </p>
          <p className="text-2xl font-bold mt-1">{formatCurrency(summary.total)}</p>
          <p className="text-sm opacity-80 mt-1">{summary.count} transaction{summary.count !== 1 ? 's' : ''}</p>
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {(Object.keys(filterLabels) as FilterPeriod[]).map((key) => (
          <button
            key={key}
            onClick={() => setFilter(key)}
            className={`px-3 py-1 rounded-full text-sm border whitespace-nowrap transition-colors ${
              filter === key
                ? 'bg-emerald-600 text-white border-emerald-600'
                : 'border-gray-200 text-gray-600 hover:bg-emerald-50 hover:border-emerald-200'
            }`}
          >
            {filterLabels[key]}
          </button>
        ))}
      </div>

      {/* Expense List */}
      {isLoading ? (
        <div className="text-center py-12 text-gray-500">Loading...</div>
      ) : expenses.length === 0 ? (
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <p className="text-gray-500 text-sm text-center py-12">
            No expenses yet. Tap "Add" to get started! 💰
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {Object.entries(groupedExpenses)
            .sort(([a], [b]) => b.localeCompare(a))
            .map(([date, items]) => (
              <div key={date}>
                <p className="text-xs font-medium text-gray-500 mb-2 uppercase">
                  {formatDate(date)}
                </p>
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 divide-y divide-gray-50">
                  {items.map((expense) => (
                    <div
                      key={expense.id}
                      className="p-3 flex items-center justify-between hover:bg-gray-50 transition-colors cursor-pointer"
                      onClick={() => openEditModal(expense)}
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-xl">
                          {expense.category_icon || '📦'}
                        </span>
                        <div>
                          <p className="text-sm font-medium text-gray-900">
                            {expense.description || expense.category_name || 'Expense'}
                          </p>
                          <p className="text-xs text-gray-500">
                            {expense.category_name || 'Uncategorized'}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-semibold text-gray-900">
                          {formatCurrency(expense.amount)}
                        </p>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleDelete(expense.id)
                          }}
                          className="text-gray-400 hover:text-red-500 p-1"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
        </div>
      )}

      {/* Add/Edit Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-end sm:items-center justify-center z-50">
          <div className="bg-white w-full sm:max-w-md sm:rounded-xl rounded-t-xl p-5 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">
                {editingExpense ? 'Edit Expense' : 'Add Expense'}
              </h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="bg-red-50 text-red-600 text-sm p-3 rounded-lg">
                  {error}
                </div>
              )}

              {/* Amount */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Amount (₦)
                </label>
                <input
                  type="number"
                  inputMode="decimal"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  placeholder="0.00"
                  className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 text-lg"
                  required
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description (optional)
                </label>
                <input
                  type="text"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="e.g. Lunch at Mr Biggs"
                  className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                />
              </div>

              {/* Category */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Category
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {categories.map((cat) => (
                    <button
                      key={cat.id}
                      type="button"
                      onClick={() => setCategoryId(cat.id)}
                      className={`p-2 rounded-lg border text-center transition-colors ${
                        categoryId === cat.id
                          ? 'border-emerald-500 bg-emerald-50 text-emerald-700'
                          : 'border-gray-200 hover:bg-gray-50'
                      }`}
                    >
                      <span className="text-xl block">{cat.icon || '📦'}</span>
                      <span className="text-xs truncate block">{cat.name}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Date */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Date
                </label>
                <input
                  type="date"
                  value={expenseDate}
                  onChange={(e) => setExpenseDate(e.target.value)}
                  className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                />
              </div>

              {/* Submit */}
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full bg-emerald-600 text-white py-3 rounded-lg font-medium hover:bg-emerald-700 disabled:opacity-50 transition-colors"
              >
                {isSubmitting ? 'Saving...' : editingExpense ? 'Update Expense' : 'Add Expense'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
