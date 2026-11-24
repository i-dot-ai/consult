import type { Question } from "./types";
import type { QuestionDetailV2 } from "./queries/questions/types";

export const getQuestionText = (
  question: Question | QuestionDetailV2,
): string =>
  "question_text" in question ? question.question_text : (question.text ?? "");

// A hybrid's answers live on its closed sibling, which is charted itself, so an
// open question is never charted even though its payload carries the answers.
export const holdsOwnAnswers = (
  question: Question | QuestionDetailV2,
): boolean =>
  "type" in question ? question.type !== "open" : !question.has_free_text;
