import { createRawSnippet } from "svelte";

import Accordion from "./Accordion.svelte";

const createSnippetWithDefault = (html: string) => {
  try {
    return createRawSnippet(() => ({
      render: () => html,
    }));
  } catch {
    return createRawSnippet(() => ({
      render: () => "<p>Child Element</p>",
    }));
  }
};

const titleHtml = $state(`<span>Accordion Title</span>`);
const titleComponent = $derived.by(() => {
  return createSnippetWithDefault(titleHtml);
});

const contentHtml = $state(`<p>Panel Content</p>`);
const contentComponent = $derived.by(() => {
  return createSnippetWithDefault(contentHtml);
});

export default {
  name: "Accordion",
  component: Accordion,
  props: [
    {
      name: "title",
      value: titleComponent,
      type: "html",
      rawHtml: titleHtml,
    },
    {
      name: "content",
      value: contentComponent,
      type: "html",
      rawHtml: contentHtml,
    },
  ],
  stories: [
    /* TODO: Add stories */
  ],
};
