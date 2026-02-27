import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { expensesApi, categoriesApi, gamificationApi, educationApi } from '../services/api'

// === Expenses ===
export function useExpenses(params?: { start_date?: string; end_date?: string; category_id?: number }) {
  return useQuery({
    queryKey: ['expenses', params],
    queryFn: () => expensesApi.list(params).then((res) => res.data),
  })
}

export function useExpenseSummary(period: 'daily' | 'weekly' | 'monthly' = 'monthly') {
  return useQuery({
    queryKey: ['expense-summary', period],
    queryFn: () => expensesApi.summary(period).then((res) => res.data),
  })
}

export function useCreateExpense() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: expensesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
      queryClient.invalidateQueries({ queryKey: ['expense-summary'] })
    },
  })
}

export function useDeleteExpense() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => expensesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
      queryClient.invalidateQueries({ queryKey: ['expense-summary'] })
    },
  })
}

// === Categories ===
export function useCategories() {
  return useQuery({
    queryKey: ['categories'],
    queryFn: () => categoriesApi.list().then((res) => res.data),
  })
}

// === Gamification ===
export function useUserStats() {
  return useQuery({
    queryKey: ['user-stats'],
    queryFn: () => gamificationApi.getStats().then((res) => res.data),
  })
}

export function useMyBadges() {
  return useQuery({
    queryKey: ['my-badges'],
    queryFn: () => gamificationApi.getMyBadges().then((res) => res.data),
  })
}

// === Education ===
export function useDailyTip() {
  return useQuery({
    queryKey: ['daily-tip'],
    queryFn: () => educationApi.getDailyTip().then((res) => res.data),
  })
}
