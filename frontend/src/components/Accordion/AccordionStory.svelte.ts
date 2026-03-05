import { createRawSnippet } from "svelte";

import Accordion from "./Accordion.svelte";
import Lightbulb2 from "../svg/material/Lightbulb2.svelte";

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
    {
      name: "With Icon",
      props: {
        title: titleComponent,
        content: contentComponent,
        Icon: Lightbulb2,
      },
    },
    {
      name: "Variant Warning",
      props: {
        title: titleComponent,
        content: contentComponent,
        variant: "warning",
        Icon: Lightbulb2,
      },
    },
    {
      name: "Variant Gray",
      props: {
        title: titleComponent,
        content: contentComponent,
        variant: "gray",
        Icon: Lightbulb2,
      },
    },
    {
      name: "Variant Light",
      props: {
        title: titleComponent,
        content: contentComponent,
        variant: "light",
        Icon: Lightbulb2,
      },
    },
    {
      name: "With Close",
      props: {
        title: titleComponent,
        content: contentComponent,
        Icon: Lightbulb2,
        onClose: () => alert("Close button clicked"),
      },
    },
    {
      name: "With Close Warning",
      props: {
        title: titleComponent,
        content: contentComponent,
        Icon: Lightbulb2,
        variant: "warning",
        onClose: () => alert("Close button clicked"),
      },
    },
  ],
};
