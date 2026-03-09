import { createRawSnippet } from "svelte";

import Accordion from "./Accordion.svelte";
import LightbulbTwo from "../svg/material/LightbulbTwo.svelte";

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
        Icon: LightbulbTwo,
      },
    },
    {
      name: "Variant Warning",
      props: {
        title: titleComponent,
        content: contentComponent,
        variant: "warning",
        Icon: LightbulbTwo,
      },
    },
    {
      name: "Variant Gray",
      props: {
        title: titleComponent,
        content: contentComponent,
        variant: "gray",
        Icon: LightbulbTwo,
      },
    },
    {
      name: "Variant Light",
      props: {
        title: titleComponent,
        content: contentComponent,
        variant: "light",
        Icon: LightbulbTwo,
      },
    },
    {
      name: "With Close",
      props: {
        title: titleComponent,
        content: contentComponent,
        Icon: LightbulbTwo,
        onClose: () => alert("Close button clicked"),
      },
    },
    {
      name: "With Close Warning",
      props: {
        title: titleComponent,
        content: contentComponent,
        Icon: LightbulbTwo,
        variant: "warning",
        onClose: () => alert("Close button clicked"),
      },
    },
  ],
};
