export const parseEmails = (input: string): string[] => {
  return input
    .split(/[,\s]+/)
    .map((email) => email.trim())
    .filter((email) => email.length > 0);
};
