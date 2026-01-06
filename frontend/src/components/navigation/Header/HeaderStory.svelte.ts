import ConsultIcon from "../../svg/ConsultIcon.svelte";
import Header from "./Header.svelte";

import { testData } from "./testData";
import TestEndItems from "./TestEndItems.svelte";

export default {
  name: "NavigationHeader",
  component: Header,
  category: "Navigation",
  props: [
    { name: "title", value: "Consult", type: "text" },
    {
      name: "subtitle",
      value: "AI safety and governance framework 2024",
      type: "text",
    },
    { name: "icon", value: ConsultIcon },
    { name: "pathParts", value: ["Dashboard"], type: "json" },
    { name: "navItems", value: testData.navItems, type: "json" },
  ],
  stories: [
    {
      name: "Default",
      props: {},
    },
    {
      name: "Consult",
      props: {
        title: "Consult",
        subtitle: "AI safety and governance framework 2024",
        icon: ConsultIcon,
        pathParts: ["Dashboard"],
        navItems: testData.navItems,
        endItems: TestEndItems,
      },
    },
  ],
};
