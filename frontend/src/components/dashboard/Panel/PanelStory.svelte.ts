import { createRawSnippet } from "svelte";

import Panel from "./Panel.svelte";

let variant = $state("default");
let childrenHtml = $state("<p>Child Element</p>");
let border = $state(true);
let bg = $state(false);
let level = $state(1);

let childrenComponent = $derived.by(() => {
  try {
    return createRawSnippet(() => ({
      render: () => childrenHtml,
    }));
  } catch {
    return createRawSnippet(() => ({
      render: () => "<p>Child Element</p>",
    }));
  }
});

export default {
  name: "Panel",
  component: Panel,
  props: [
    {
      name: "variant",
      value: variant,
      type: "select",
      options: [
        { value: "default", label: "Default" },
        { value: "primary", label: "Primary" },
        { value: "approve", label: "Approve" },
      ],
    },
    {
      name: "border",
      value: border,
      type: "bool",
    },
    {
      name: "bg",
      value: bg,
      type: "bool",
    },
    {
      name: "level",
      value: level,
      type: "number",
    },
    {
      name: "children",
      value: childrenComponent,
      type: "html",
      rawHtml: childrenHtml,
    },
  ],
  stories: [
    // {
    //     name: "Default",
    //     props: {
    //         title: "Default Title",
    //         description: "Default story description",
    //         tags: ["Tag 1", "Tag 2"],
    //         highlightText: "",
    //     },
    // },
  ],
};
