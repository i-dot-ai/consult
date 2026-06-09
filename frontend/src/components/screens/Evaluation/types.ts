export type EvalStatus =
  | "insufficient_data"
  | "below_benchmark"
  | "meets_benchmark";

export type F1Stats = {
  mean: number;
  ci_lower: number | null;
  ci_upper: number | null;
  approximate: boolean;
};

export type QuestionEval = {
  id: string;
  number: number;
  text: string;
  status: EvalStatus;
  responses: number;
  responses_read: number;
  responses_edited: number;
  f1: F1Stats | null;
  f1_all_themes: F1Stats | null;
};

export type EvalUser = {
  id: string;
  email: string;
};

export type ConsultationEval = {
  id: string;
  title: string;
  config: {
    benchmark_f1: number;
    min_sample_size: number;
  };
  users: EvalUser[];
  summary: {
    status: EvalStatus;
    responses: number;
    responses_read: number;
    responses_edited: number;
    f1: F1Stats | null;
    f1_all_themes: F1Stats | null;
  };
  questions: QuestionEval[];
};
