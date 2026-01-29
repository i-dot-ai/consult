import { ConsultationStageNames } from "../../../global/types";
import HeaderConsult from "./HeaderConsult.svelte";

const TITLE = "Consult";
const SUBTITLE = "AI safety and governance framework 2024";

export default {
  name: "HeaderConsult",
  component: HeaderConsult,
  category: "Navigation",
  props: [
    { name: "title", value: "Consult", type: "text" },
    { name: "path", value: "Dashboard", type: "text" },
    { name: "isSignedIn", value: true, type: "bool" },
    { name: "isStaff", value: true, type: "bool" },
    { name: "showProcess", value: true, type: "bool" },
    {
      name: "consultationStage",
      value: ConsultationStageNames.THEME_MAPPING,
      type: "text",
    },
  ],
  stories: [
    {
      name: "Not Signed In",
      props: {
        title: TITLE,
        subtitle: SUBTITLE,
        isSignedIn: false,
        showProcess: false,
      },
    },
    {
      name: "Signed In As Staff",
      props: {
        title: TITLE,
        subtitle: SUBTITLE,
        isSignedIn: false,
        showProcess: false,
        isStaff: true,
      },
    },
    {
      name: "Signed In With Process",
      props: {
        title: TITLE,
        subtitle: SUBTITLE,
        isSignedIn: true,
        showProcess: true,
      },
    },
    {
      name: "Signed In Without Process",
      props: {
        title: TITLE,
        subtitle: SUBTITLE,
        isSignedIn: true,
        showProcess: false,
      },
    },
  ],
};
