import ButtonTest from "./ButtonTest.svelte";
import { createRawSnippet } from "svelte";

let variant = $state("default");
let highlighted = $state(false);
let highlightVariant = $state("dark");
let disabled = $state(false);

const children = createRawSnippet(() => ({
    render: () => "<p>Button Text</p>",
}));
const handleClick = () => console.log("handleClick is called");

export default {
  name: "Button",
  component: ButtonTest,
  category: "Inputs",
  props: [
    { name: "variant", value: variant, type: "select", options: [
        { value: "default", label: "default" },
        { value: "gray", label: "gray" },
        { value: "primary", label: "primary" },
        { value: "ghost", label: "ghost" },
        { value: "approve", label: "approve" },
        { value: "outline", label: "outline" },
        { value: "warning", label: "warning" },
        { value: "danger", label: "danger" },
        { value: "dot", label: "dot" },
        { value: "text", label: "text" },
    ] },
    { name: "highlighted", value: highlighted, type: "bool" },
    { name: "highlightVariant", value: highlightVariant, type: "select", options: [
        { value: "dark", label: "dark" },
        { value: "light", label: "light" },
        { value: "primary", label: "primary" },
        { value: "approve", label: "approve" },
        { value: "none", label: "none" },
    ]},
    { name: "disabled", value: disabled, type: "bool" },
    { name: "handleClick", value: handleClick, type: "func" },
    { name: "children", value: children, type: "func" },
  ],
  stories: [],
};
