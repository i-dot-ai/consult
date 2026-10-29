export const SHORT_NAME_LIMIT = 40;

export function shortNameProblem(
  name: string,
  questionNumber: number,
  takenNames: Map<string, number>,
  required: boolean,
): string {
  const trimmed = name.trim();
  if (!trimmed) {
    return required
      ? "Enter a short name. This is what labels the filter on your dashboard."
      : "";
  }
  if (trimmed.length > SHORT_NAME_LIMIT) {
    return `This is ${trimmed.length} characters. Keep it under ${SHORT_NAME_LIMIT} so it fits the dashboard.`;
  }
  const takenBy = takenNames.get(trimmed.toLowerCase());
  if (takenBy !== undefined && takenBy !== questionNumber) {
    return `Question ${takenBy} already uses this name. Two filters with the same label cannot be told apart.`;
  }
  return "";
}
