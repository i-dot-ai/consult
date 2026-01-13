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

export const getClientId = (): string => {
  // Try runtime environment variable first (for server-side)
  if (
    typeof process !== "undefined" &&
    process.env?.PUBLIC_INTERNAL_ACCESS_CLIENT_ID
  ) {
    return process.env.PUBLIC_INTERNAL_ACCESS_CLIENT_ID;
  }

  // Fall back to build-time public env var (for client-side)
  const client_id = import.meta.env.PUBLIC_INTERNAL_ACCESS_CLIENT_ID;
  if (client_id) {
    return client_id;
  }

  throw new Error(
    "PUBLIC_INTERNAL_ACCESS_CLIENT_ID environment variable is not set. This is required for the application to function.",
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

export const formatDate = (dateStr: string) => {
  const date = new Date(dateStr);
  return date.toLocaleString("en-GB", {
    dateStyle: "long",
    timeStyle: "short",
  });
};

export const isKeyPressed = (
  event: KeyboardEvent,
  possibleValues: (string | number)[],
) => {
  const eventKey = event.key || event.code || event.keyCode;
  return possibleValues.includes(eventKey);
};

export const handleEnterOrSpacePress = (
  event: KeyboardEvent,
  callback: () => void,
) => {
  const isEnter = isKeyPressed(event, ["Enter", "Return", 13]);
  const isSpace = isKeyPressed(event, [" ", "Spacebar", 32]);

  // Enter or Space pressed
  if (isEnter || isSpace) {
    event.preventDefault();
    callback();
  }
};
export const handleEscKeyPress = (
  event: KeyboardEvent,
  callback: () => void,
) => {
  // Esc key pressed
  if (isKeyPressed(event, ["Escape", "Esc", 27])) {
    event.preventDefault();
    callback();
  }
};
export const getTimeDeltaInMinutes = (
  laterDate: Date,
  earlierDate: Date,
): number => {
  const MILLISECONDS_PER_MINUTE = 60000;
  const delta = laterDate.getTime() - earlierDate.getTime();
  return Math.floor(delta / MILLISECONDS_PER_MINUTE);
};

export const formatTimeDeltaText = (minutes: number): string => {
  const MINUTES_IN_HALF_HOUR = 30;
  const MINUTES_IN_HOUR = MINUTES_IN_HALF_HOUR * 2;
  const MINUTES_IN_DAY = MINUTES_IN_HOUR * 24;
  const MINUTES_IN_MONTH = MINUTES_IN_DAY * 30;
  const MINUTES_IN_YEAR = MINUTES_IN_MONTH * 12;

  // Exceptional cases
  if (minutes >= MINUTES_IN_HALF_HOUR && minutes < MINUTES_IN_HOUR) {
    return `less than an hour`;
  }
  if (minutes < 1) {
    return `a moment`;
  }

  let value: number = minutes;
  let unit: "minute" | "hour" | "day" | "month" | "year" = "minute";

  if (minutes < MINUTES_IN_HOUR) {
    value = minutes;
    unit = "minute";
  } else if (minutes >= MINUTES_IN_HOUR && minutes < MINUTES_IN_DAY) {
    value = minutes / MINUTES_IN_HOUR;
    unit = "hour";
  } else if (minutes >= MINUTES_IN_DAY && minutes < MINUTES_IN_MONTH) {
    value = minutes / MINUTES_IN_DAY;
    unit = "day";
  } else if (minutes >= MINUTES_IN_MONTH && minutes < MINUTES_IN_YEAR) {
    value = minutes / MINUTES_IN_MONTH;
    unit = "month";
  } else if (minutes >= MINUTES_IN_YEAR) {
    value = minutes / MINUTES_IN_YEAR;
    unit = "year";
  }
  return `${Math.floor(value)} ${unit}${value > 1 ? "s" : ""}`;
};

export const derandomize = (
  container: HTMLElement,
  attrs: string[],
  newValue = "fixed-value",
) => {
  // Replaces randomly generated attribute values with fixed values
  // to allow consistent snapshot testing

  attrs.forEach((attr) => {
    container
      .querySelectorAll(`*[${attr}]`)
      .forEach((el) => el.setAttribute(attr, newValue));
  });
};

export function debounce<T extends (...args: unknown[]) => void>(
  callback: T,
  delay: number,
) {
  let timeoutId: ReturnType<typeof setTimeout> | null = null;

  return (...args: Parameters<T>) => {
    if (timeoutId !== null) {
      clearTimeout(timeoutId);
    }

    timeoutId = setTimeout(() => {
      timeoutId = null;
      callback(...args);
    }, delay);
  };
}
