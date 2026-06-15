import Breadcrumbs from "./Breadcrumbs.svelte";

export default {
  name: "Breadcrumbs",
  component: Breadcrumbs,
  category: "Navigation",
  props: [{ name: "consultationStage", value: "analysis", type: "text" }],
  stories: [
    {
      name: "Stage Finalising Themes",
      props: { consultationStage: "finalising_themes" },
    },
    {
      name: "Stage Assigning Themes (AI)",
      props: { consultationStage: "assigning_themes" },
    },
    {
      name: "Stage Analysis",
      props: { consultationStage: "analysis" },
    },
  ],
};
