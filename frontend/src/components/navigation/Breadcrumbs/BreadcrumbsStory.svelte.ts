import Breadcrumbs from "./Breadcrumbs.svelte";

export default {
  name: "Breadcrumbs",
  component: Breadcrumbs,
  category: "Navigation",
  props: [{ name: "consultationStage", value: "analysis", type: "text" }],
  stories: [
    {
      name: "Stage Finalising Themes",
      props: { consultationStage: "theme_sign_off" },
    },
    {
      name: "Stage Assigning Themes (AI)",
      props: { consultationStage: "theme_mapping" },
    },
    {
      name: "Stage Analysis",
      props: { consultationStage: "analysis" },
    },
  ],
};
