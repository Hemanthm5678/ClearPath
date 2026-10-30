export type ConfusionState = 'focused' | 'hesitant' | 'confused';

export interface ConfusionData {
  score: number;
  state: ConfusionState;
  reasons: string[];
}

export interface ActionWhy {
  signals: string[];
  decision: string;
  prereq: string | null;
}

export interface ActionData {
  type: 'continue' | 'hint' | 're_explain' | 'prereq_scaffold' | 'encourage';
  style: 'visual' | 'analogy' | 'step_by_step' | 'simple_language' | 'none';
  level: number;
  why: ActionWhy;
}

export interface TutorData {
  explanation: string;
  check_question: string;
  visual_description: string;
  source: 'groq' | 'cache' | 'offline_bank';
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
  difficulty: 'easy' | 'medium' | 'hard';
  prompt: string;
  type: 'multiple_choice' | 'numeric';
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
  state: ConfusionState;
  why: string;
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
