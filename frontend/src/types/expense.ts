// Expense-related types

export interface Category {
  id: number
  name: string
  icon: string | null
  color: string | null
  is_custom: boolean
}

export interface Expense {
  id: number
  amount: number
  currency: string
  description: string | null
  expense_date: string
  category_id: number | null
  category_name: string | null
  category_icon: string | null
  source: 'manual' | 'whatsapp' | 'bank_sync'
  created_at: string
}

export interface ExpenseSummary {
  total: number
  count: number
  by_category: Record<string, number>
  period: 'daily' | 'weekly' | 'monthly'
  start_date: string
  end_date: string
}

export interface ExpenseCreate {
  amount: number
  description?: string
  category_id?: number
  expense_date?: string
}

export interface ExpenseUpdate {
  amount?: number
  description?: string
  category_id?: number
  expense_date?: string
}

// AI-Powered Features
export interface AIStatus {
  configured: boolean
  model: string
  features: string[]
}

export interface ParsedExpense {
  amount: number | null
  description: string | null
  category: string
  category_id: number | null
  confidence: number
}

export interface ReceiptData {
  merchant: string | null
  amount: number | null
  items: string[]
  date: string | null
  category: string
  category_id: number | null
  confidence: number
}

export interface SmartExpenseCreate {
  text?: string
  amount?: number
  description?: string
  category_id?: number
  expense_date?: string
  use_ai?: boolean
}
