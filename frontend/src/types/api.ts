export type ConfusionState = 'calm' | 'focused' | 'mild' | 'uncertain' | 'hesitant' | 'confused' | 'lost' | string;

export type CognitiveState = 'GAMING' | 'BORED' | 'CONFUSED' | 'NATURALLY_SLOW' | 'FOCUSED';

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
  type: 'continue' | 'hint' | 're_explain' | 'prereq_scaffold' | 'encourage' | 'break' | 'gaming_cooldown' | 'challenge_booster' | string;
  style?: 'visual' | 'analogy' | 'step_by_step' | 'simple_language' | 'none' | string;
  level?: number;
  why: ActionWhy | Record<string, any> | string;
  cooldown_seconds?: number;
}

export interface TutorData {
  explanation: string;
  check_question?: string;
  visual_description?: string;
  source: 'groq' | 'cache' | 'offline_bank' | 'telemetry_guard' | string;
}

export interface InterventionEfficacy {
  status: 'HELPED' | 'UNRESOLVED' | 'MONITORING' | string;
  state_before?: string;
  state_after?: string;
  delta_time_ratio?: number;
  delta_accuracy?: number;
  summary_text?: string;
}

export interface TelemetryMetrics {
  actual_time_sec: number;
  expected_time_sec: number;
  complexity_weight: number;
  student_pace_factor: number;
  normalized_time_ratio: number;
  cognitive_state: CognitiveState;
  cooldown_seconds: number;
}

export interface EventResponse {
  confusion: ConfusionData;
  mastery: Record<string, number>;
  action: ActionData;
  tutor?: TutorData | null;
  telemetry?: TelemetryMetrics;
  intervention_efficacy?: InterventionEfficacy;
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
  expected_time_sec?: number;
  complexity_weight?: number;
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

export interface SimulateResponse {
  status: string;
  session_id: string;
  student_name: string;
  profile: string;
  concept_id: string;
  confusion_score: number;
  confusion_state: string;
  mastery: Record<string, number>;
  question?: Question;
}

export interface HeatmapCell {
  confusion: number;
  why: string;
  state?: ConfusionState;
  cognitive_state?: CognitiveState;
  breakdown?: string;
  efficacy?: InterventionEfficacy;
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

export interface WebSocketMeterMessage {
  score: number;
  state: ConfusionState;
  cognitive_state?: CognitiveState;
  student_pace_factor?: number;
  normalized_time_ratio?: number;
  cooldown_seconds?: number;
  intervention_efficacy?: InterventionEfficacy;
}

export interface User {
  id: string;
  name: string;
  email: string;
  role: 'student' | 'teacher';
  created_at?: number;
}

export interface DemoUser extends User {
  password?: string;
  description?: string;
}

export interface AuthResponse {
  status: string;
  user: User;
  token: string;
  message?: string;
}

export interface CreateQuestionRequest {
  concept_id: string;
  prompt: string;
  options: string[];
  correct_answer: string;
  difficulty?: 'auto' | 'easy' | 'medium' | 'hard' | string;
}

export interface QuestionAnalysis {
  complexity_tier: string;
  expected_time_sec: number;
  complexity_weight: number;
  hint: string;
  step_by_step: string;
  source?: string;
  explanations: {
    visual: { explanation: string; check_question: string; visual_description: string };
    analogy: { explanation: string; check_question: string; visual_description: string };
    step_by_step: { explanation: string; check_question: string; visual_description: string };
    simple_language: { explanation: string; check_question: string; visual_description: string };
  };
}

export interface CreateQuestionResponse {
  status: string;
  question: Question;
  analysis: QuestionAnalysis;
  message: string;
}


