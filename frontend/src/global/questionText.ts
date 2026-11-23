import type { Question } from "./types";
import type { QuestionDetailV2 } from "./queries/questions/types";

export const getQuestionText = (
  question: Question | QuestionDetailV2,
): string =>
  "question_text" in question ? question.question_text : (question.text ?? "");
