export const getEnv = (url: string): string => {
  if (url.includes("consult-dev.ai.cabinetoffice.gov.uk")) {
    return "dev";
  }
  if (url.includes("consult.ai.cabinetoffice.gov.uk")) {
    return "prod";
  }
  return "local";
};

export const getBackendUrl = (): string => {
  // Try runtime environment variable first (for server-side)
  if (typeof process !== "undefined" && process.env?.BACKEND_URL) {
    return process.env.BACKEND_URL;
  }

  // Fall back to build-time public env var (for client-side)
  const backendUrl = import.meta.env.PUBLIC_BACKEND_URL;
  if (backendUrl) {
    return backendUrl;
  }

  throw new Error(
    "BACKEND_URL environment variable is not set. This is required for the application to function.",
  );
};

export const applyHighlight = (
  fullText: string,
  matchedText: string,
): string => {
  if (!matchedText) {
    return fullText;
  }
  const regex = new RegExp(matchedText, "gi");
  return fullText.replace(
    regex,
    (match) => `<span class="bg-yellow-300">${match}</span>`,
  );
};

export const getPercentage = (
  partialValue: number,
  totalValue: number,
): number => {
  if (!totalValue) {
    return 0;
  }
  const percentage = (partialValue / totalValue) * 100;

  // Round to 1 decimal point
  return Math.round(percentage * 10) / 10;
};

export const toTitleCase = (text: string): string => {
  return text
    .replace("-", " ")
    .replace(
      /\w\S*/g,
      (text) => text.charAt(0).toUpperCase() + text.substring(1).toLowerCase(),
    );
};

export function paginateArray(arr: unknown[] | undefined, size: number) {
  if (!arr || arr.length === 0) {
    return [];
  }
  return arr.reduce((acc: unknown[][], curr, i) => {
    const index = Math.floor(i / size);
    const page = acc[index] || (acc[index] = []);
    page.push(curr);

    return acc;
  }, []);
}

export function flattenArray(items: any[]): any[] {
  if (!items) {
    return [];
  }

  const result = [];

  for (const item of items) {
    const { children, ...attrs } = item;
    result.push(attrs);

    if (children?.length > 0) {
      result.push(...flattenArray(children));
    }
  }

  return result;
}

export const formatDate = (dateStr: string) => {
  const date = new Date(dateStr);
  return date.toLocaleString("en-GB", {
    dateStyle: "long",
    timeStyle: "short",
  });
};
