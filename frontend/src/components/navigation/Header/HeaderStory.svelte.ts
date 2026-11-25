import ConsultLogo from "../../svg/ConsultLogo.svelte";
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
    { name: "icon", value: ConsultLogo },
    { name: "pathParts", value: ["Dashboard"], type: "json" },
    { name: "navItems", value: testData.navItems, type: "json" },
    { name: "showTitle", value: false, type: "bool" },
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
        icon: ConsultLogo,
        pathParts: ["Dashboard"],
        navItems: testData.navItems,
        endItems: TestEndItems,
        showTitle: false,
      },
    },
  ],
};
