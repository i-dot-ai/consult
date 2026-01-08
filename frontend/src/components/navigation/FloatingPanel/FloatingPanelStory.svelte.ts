import FloatingPanel from "./FloatingPanel.svelte";
import FloatingPanelContent from "../FloatingPanelContent/FloatingPanelContent.svelte";

const direction = $state("left");

export default {
  name: "FloatingPanel",
  component: FloatingPanel,
  category: "Navigation",
  props: [
    {
      name: "direction",
      value: direction,
      type: "select",
      options: [
        { value: "left", label: "left" },
        { value: "right", label: "right" },
      ],
    },
    {
      name: "children",
      value: FloatingPanelContent,
    },
  ],
  stories: [
    {
      name: "Left Direction",
      props: {
        direction: "left",
        children: FloatingPanelContent,
      },
    },
    {
      name: "Right Direction",
      props: {
        direction: "right",
        children: FloatingPanelContent,
      },
    },
  ],
};
