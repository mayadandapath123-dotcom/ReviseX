/** Mirror of the API contracts. Keep in sync with backend/app/api. */

export type Difficulty = 'easy' | 'medium' | 'hard'
export type QuestionType = 'mcq_single' | 'balancing' | 'numeric_input'

export interface QuestionOption {
  key: string
  text: string
  is_correct?: boolean
  render?: Record<string, unknown>
}

export interface Question {
  id: string
  subject: string
  subject_name: string
  branch: string
  branch_name: string
  chapter: string
  chapter_name: string
  topic: string | null
  topic_name: string | null
  question_type: QuestionType
  prompt: string
  stimulus: Record<string, any>
  difficulty: Difficulty
  time_budget_ms: number
  syllabus_status: string
  tags: string[]
  options: QuestionOption[]
  answer_key: string
  explanation: string | null
  hint: string | null
}

export interface TestMode {
  key: string
  name: string
  description: string
  icon: string | null
  group: string
  featured: boolean
  quick_start: boolean
  duration_limit_ms: number | null
  question_count: number | null
  filters: Record<string, any>
  scoring: Record<string, any>
}

export interface StartTestResponse {
  session_id: string
  mode: TestMode | null
  config: Record<string, any>
  duration_limit_ms: number | null
  per_question_time_ms: number | null
  max_attempts: number
  show_explanation: string
  wrong_penalty: number
  stop_on_time: boolean
  questions_total: number
  questions: Question[]
  server_time: string
}

export interface AttemptPayload {
  seq: number
  question_id: string
  selected_key: string | null
  option_order: string[]
  response_ms: number
  shown_ms: number
  coefficients?: number[]
}

export interface SessionSummary {
  score: number
  xp: number
  correct: number
  answered: number
  accuracy: number
  avg_response_ms: number
  fastest_response_ms: number | null
  best_streak: number
  completion_bonus: number
  accuracy_bonus: number
}

export interface TopicArea {
  topic_id: string
  name: string
  attempts: number
  correct: number
  accuracy: number
}

export interface SessionEvent {
  kind: string
  [key: string]: any
}

export interface SubmitResponse {
  session_id: string
  summary: SessionSummary
  analysis: {
    xp_awarded: number
    level: number
    level_info: LevelInfo
    events: SessionEvent[]
    personal_bests: any[]
    weak_areas: TopicArea[]
    strong_areas: TopicArea[]
  }
  attempts: Array<{
    question_id: string
    is_correct: boolean
    points: number
    response_ms: number
    correct_answer: string
    explanation: string | null
  }>
}

export interface LevelInfo {
  level: number
  name: string
  xp: number
  xp_into_level: number
  xp_for_next_level: number
  level_progress: number
}

export interface Profile {
  id: string
  /** Set once the profile belongs to an account; null in local, account-free mode. */
  user_id?: string | null
  display_name: string
  avatar: string | null
  is_active: boolean
  xp_total: number
  level: number
  day_streak: number
  questions_answered?: number
  accuracy?: number
  sessions?: number
  settings?: Record<string, any>
}

export interface TopicNode {
  id: string
  name: string
  mastery: number
  attempts: number
  confidence: number
  bank_size?: number
  accuracy?: number
}

export interface ChapterNode {
  id: string
  code: string | null
  name: string
  syllabus_status: string
  bank_size: number
  attempts: number
  accuracy: number
  mastery: number
  topics: TopicNode[]
}

export interface BranchNode {
  id: string
  name: string
  icon: string | null
  is_active: boolean
  chapters: ChapterNode[]
  question_count: number
}

export interface SubjectNode {
  id: string
  name: string
  icon: string | null
  is_active: boolean
  note: string | null
  branches: BranchNode[]
  question_count: number
}

export interface Dashboard {
  today: { day: string; questions: number; accuracy: number; avg_response_ms: number; xp_today: number; sessions_today: number }
  lifetime: {
    questions_answered: number; correct_answers: number; accuracy: number; avg_response_ms: number
    fastest_response_ms: number | null; sessions_completed: number; total_score: number
    xp_total: number; level: number; day_streak: number
  }
  level: LevelInfo
  day_streak: number
  srs: { due: number; by_state: Record<string, number> }
  suggestions: {
    continue: null | { kind: string; reason: string; label: string; chapter_id?: string; chapter_name?: string; branch?: string; topic_id?: string; mastery?: number | null; suggested_mode: string }
    weak_topics: any[]
    unpractised: any[]
  }
  recent_sessions: any[]
  mistakes: { total: number; open: number; by_branch: any[] }
}

export interface Mistake {
  question_id: string
  prompt: string
  question_type: string
  difficulty: string
  answer_key: string
  explanation: string | null
  topic_name: string | null
  chapter_name: string
  branch_name: string
  wrong_count: number
  resolved: boolean
}
