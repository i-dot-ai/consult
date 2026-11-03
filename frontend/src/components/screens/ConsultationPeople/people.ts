import type {
  ConsultationV2,
  ConsultationV2User,
} from "../../../global/queries/consultations/types";

export const EMAIL_PATTERN = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

export type AddResult = { outcome: "added" } | { outcome: "failed" };

export function orderPeople(
  consultation: ConsultationV2,
): ConsultationV2User[] {
  const creator = consultation.created_by;
  if (!creator) {
    return consultation.users;
  }
  const others = consultation.users.filter(
    (person) => person.id !== creator.id,
  );
  return [creator, ...others];
}

export function getPeopleCountText(count: number): string {
  if (count === 1) {
    return "1 person";
  }
  return `${count} people`;
}

const NAMED_EMAILS_LIMIT = 3;

function listEmails(emails: string[]): string {
  if (emails.length <= NAMED_EMAILS_LIMIT) {
    return emails.join(", ");
  }
  const others = emails.length - NAMED_EMAILS_LIMIT;
  const noun = others === 1 ? "other" : "others";
  return `${emails.slice(0, NAMED_EMAILS_LIMIT).join(", ")} and ${others} ${noun}`;
}

export function getAddedNotice(
  addedCount: number,
  alreadyOnEmails: string[],
): string {
  let added = "Nobody added.";
  if (addedCount === 1) {
    added = "1 person added.";
  } else if (addedCount > 1) {
    added = `${addedCount} people added.`;
  }
  if (alreadyOnEmails.length === 0) {
    return added;
  }
  const verb = alreadyOnEmails.length === 1 ? "is" : "are";
  return `${added} ${listEmails(alreadyOnEmails)} ${verb} already on this consultation.`;
}
