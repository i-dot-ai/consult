export type QuestionType = "demographic" | "closed" | "open";
export type QuestionV2 = {
  id: string;
  number: number;
  text: string;
  type: QuestionType | null;
  closed_question: string | null;
  status: "draft" | "configured" | "finalising_themes" | "confirmed";
  response_count: number;
};
export type QuestionV2UpdateBody = {
  text?: string;
  type?: QuestionType | null;
  closed_question?: string | null;
};
