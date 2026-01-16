import { ConsultationStageNames } from "../../../global/types";
import Breadcrumbs from "./Breadcrumbs.svelte";

export default {
  name: "Breadcrumbs",
  component: Breadcrumbs,
  category: "Navigation",
  props: [{ name: "consultationStage", value: "analysis", type: "text" }],
  stories: [
    {
      name: "Stage Theme Sign Off",
      props: { consultationStage: ConsultationStageNames.THEME_SIGN_OFF },
    },
    {
      name: "Stage Theme Mapping",
      props: { consultationStage: ConsultationStageNames.THEME_MAPPING },
    },
    {
      name: "Stage Analysis",
      props: { consultationStage: ConsultationStageNames.ANALYSIS },
    },
  ],
};
