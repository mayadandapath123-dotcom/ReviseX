import { useQuery } from '@tanstack/react-query'
import { api } from './client'
import type { Dashboard, Mistake, SubjectNode, TestMode } from '@/shared/types'

export interface StartTestParams {
  mode_key?: string
  subject?: string
  branch?: string
  chapter?: string
  topic?: string
  question_count?: number
  duration_limit_ms?: number
}

export const startTest = (params: StartTestParams) => api.post<any>('/quiz/sessions', params)

export const useDashboard = () =>
  useQuery({ queryKey: ['dashboard'], queryFn: () => api.get<Dashboard>('/progress/dashboard') })

export const useModes = () =>
  useQuery({
    queryKey: ['modes'],
    queryFn: () => api.get<{ modes: TestMode[]; groups: Record<string, TestMode[]>; quick_start: TestMode[] }>('/content/modes'),
    staleTime: 10 * 60_000,
  })

export const useTree = (includeOffSyllabus = false) =>
  useQuery({
    queryKey: ['tree', includeOffSyllabus],
    queryFn: () => api.get<{ subjects: SubjectNode[] }>(`/content/tree?include_off_syllabus=${includeOffSyllabus}`),
    staleTime: 10 * 60_000,
  })

export const useMistakes = (branch?: string) =>
  useQuery({
    queryKey: ['mistakes', branch ?? 'all'],
    queryFn: () => api.get<{ mistakes: Mistake[]; stats: { total: number; open: number } }>(`/mistakes${branch ? `?branch=${branch}` : ''}`),
  })

export const useBests = () => useQuery({ queryKey: ['bests'], queryFn: () => api.get<{ personal_bests: any[] }>('/progress/bests') })
export const useBadges = () => useQuery({ queryKey: ['badges'], queryFn: () => api.get<{ badges: any[] }>('/progress/badges') })
export const useMastery = () => useQuery({ queryKey: ['mastery'], queryFn: () => api.get<{ topics: any[] }>('/progress/mastery') })
export const useLeaderboard = (scope: 'today' | 'week' | 'all' = 'today') =>
  useQuery({ queryKey: ['leaderboard', scope], queryFn: () => api.get<any>(`/leaderboard/local?scope=${scope}`) })
export const useAiStatus = () => useQuery({ queryKey: ['ai-status'], queryFn: () => api.get<any>('/ai/status'), staleTime: 5 * 60_000 })
