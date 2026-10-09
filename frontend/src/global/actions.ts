import type { Action } from "svelte/action";

/**
 * CSSOM writes bypass the CSP, unlike an inline `style` attribute blocked by style-src.
 *
 * @param vars custom property names without the `--` prefix, mapped to values.
 */
export const cssVars: Action<HTMLElement, Record<string, string | number>> = (
  node,
  vars,
) => {
  let applied: string[] = [];

  const apply = (next: Record<string, string | number>) => {
    for (const name of applied) {
      if (!(name in next)) node.style.removeProperty(`--${name}`);
    }
    applied = Object.keys(next);
    for (const [name, value] of Object.entries(next)) {
      node.style.setProperty(`--${name}`, String(value));
    }
  };

  apply(vars);

  return { update: apply };
};
