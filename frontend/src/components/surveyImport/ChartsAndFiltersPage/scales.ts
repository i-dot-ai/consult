import type { DemographicAnswer } from "../../../global/queries/questions/types";

const SCALES = [
  [
    "Strongly agree",
    "Agree",
    "Neither agree nor disagree",
    "Disagree",
    "Strongly disagree",
  ],
  [
    "Very satisfied",
    "Satisfied",
    "Neither",
    "Dissatisfied",
    "Very dissatisfied",
  ],
  ["Always", "Often", "Sometimes", "Rarely", "Never"],
];

function scaleFor(answers: DemographicAnswer[]): string[] | undefined {
  const names = new Set(answers.map((answer) => answer.text.toLowerCase()));
  return SCALES.find((scale) =>
    scale.every((step) => names.has(step.toLowerCase())),
  );
}

export function orderAnswers(answers: DemographicAnswer[]): {
  answers: DemographicAnswer[];
  isScale: boolean;
} {
  const scale = scaleFor(answers);
  if (!scale) {
    return { answers, isScale: false };
  }
  const rank = new Map(scale.map((step, index) => [step.toLowerCase(), index]));
  const ordered = [...answers].sort((first, second) => {
    const firstRank = rank.get(first.text.toLowerCase()) ?? scale.length;
    const secondRank = rank.get(second.text.toLowerCase()) ?? scale.length;
    return firstRank - secondRank;
  });
  return { answers: ordered, isScale: true };
}
