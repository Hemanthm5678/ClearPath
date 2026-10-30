export type ConfusionState = 'calm' | 'focused' | 'mild' | 'uncertain' | 'hesitant' | 'confused' | 'lost' | string;

export interface ConfusionData {
  score: number;
  state: ConfusionState;
  reasons: string[];
}

export interface ActionWhy {
  signals: string[];
  decision: string;
  prereq?: string | null;
}

export interface ActionData {
  type: 'continue' | 'hint' | 're_explain' | 'prereq_scaffold' | 'encourage' | 'break' | string;
  style?: 'visual' | 'analogy' | 'step_by_step' | 'simple_language' | 'none' | string;
  level?: number;
  why: ActionWhy;
}

export interface TutorData {
  explanation: string;
  check_question?: string;
  visual_description?: string;
  source: 'groq' | 'cache' | 'offline_bank' | string;
}

export interface EventResponse {
  confusion: ConfusionData;
  mastery: Record<string, number>;
  action: ActionData;
  tutor?: TutorData | null;
}

export interface Question {
  id: string;
  concept_id: string;
  difficulty: 'easy' | 'medium' | 'hard' | string;
  prompt: string;
  type: 'multiple_choice' | 'numeric' | string;
  options?: string[];
  correct_answer: string;
  hint?: string;
  step_by_step?: string;
}

export interface Concept {
  id: string;
  name: string;
  description: string;
  prerequisites: string[];
  order: number;
}

export interface SessionResponse {
  session_id: string;
  concept: Concept;
  question: Question;
}

export interface NextQuestionResponse {
  question: Question;
  concept: string;
  difficulty: string;
}

export interface ExplainResponse {
  explanation: string;
  check_question: string;
  visual_description: string;
  source: string;
}

export interface ChatResponse {
  reply: string;
  source: string;
}

export interface HeatmapCell {
  confusion: number;
  why: string;
  state?: ConfusionState;
}

export interface StudentSummary {
  id: string;
  name: string;
  current_concept: string;
  score: number;
  state: ConfusionState;
}

export interface HeatmapResponse {
  students: StudentSummary[];
  concepts: Concept[];
  cells: HeatmapCell[][];
}

export interface HealthStatus {
  mode: string;
  groq_ok: boolean;
  models: string[];
  cache_hits: number;
  offline_used: number;
}
