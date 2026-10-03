export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export type SessionSummary = {
  session_id: string;
  title: string;
  backend: string;
  model_id: string | null;
  turn_count: number;
  seed_count: number;
  runtime_mode: string;
};

export type Orchestration = {
  state?: string;
  reason_text?: string;
  required_action?: string | null;
};

export type SeedTimelineEvent = {
  sequence: number;
  type: string;
  timestamp?: string | null;
  payload: Record<string, unknown>;
};

export type Seed = {
  id: string;
  text: string;
  status: string;
  weight: number;
  trace: number;
  occurrence_count: number;
  evidence_count: number;
  blocking?: boolean;
  current_gate_authorized?: boolean;
  plain_explanation?: string;
  orchestration?: Orchestration;
};

export type SeedDetail = Seed & {
  authority_profile_id: string;
  effective_gate_policy_id?: string | null;
  review_required: boolean;
  plain_explanation: string;
  timeline: SeedTimelineEvent[];
};

export type SessionView = {
  session_id: string;
  title: string;
  backend: string;
  model_id: string | null;
  authority_profile_id: string;
  effective_gate_policy_id: string;
  behavior_config_digest: string;
  messages: ChatMessage[];
  seeds: Seed[];
  orchestration?: Orchestration;
};

export type CreateSessionInput = {
  title: string;
  backend: "fixture" | "ollama";
  model_id?: string;
  authority_mode: "controlled" | "assisted" | "exploratory";
  allow_same_turn_revision?: boolean;
};

export type TurnResult = {
  report: Record<string, unknown>;
  comparison: Record<string, unknown> | null;
  session: SessionView;
};
