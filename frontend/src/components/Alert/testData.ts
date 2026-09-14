import { createRawSnippet } from "svelte";
import Help from "../svg/material/Help.svelte";

export const childrenDefault = createRawSnippet(() => ({
  render: () => `<p>Child content</p>`,
}));

export const childrenLong = createRawSnippet(() => ({
  render: () => `<p>${"Long child content".repeat(20)}</p>`,
}));

export const Icon = Help;

export const children = childrenDefault;

export const defaultVariant = "info";
