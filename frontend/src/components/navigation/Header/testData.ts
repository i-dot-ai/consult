import type { Props } from "./types";

import ConsultIcon from "../../svg/ConsultIcon.svelte";

export const testData: Props = {
  title: "Consult",
  subtitle: "AI safety and governance framework 2024",
  icon: ConsultIcon,
  pathParts: ["Dashboard"],
  navItems: [
    { label: "Home", url: "/" },
    { label: "Support", children: [
      { label: "Walkthrough", url: "/walkthrough" },
      { label: "Guidance", url: "/guidance" },
      { label: "Feedback", url: "/feedback" },
      { label: "Privacy notice", url: "/privacy" },
    ]},
    { label: "Manage", children: [
      { label: "Consultations", url: "/consultations" },
      { label: "Users", url: "/users" },
    ]},
  ],
}