import Person from "../../svg/material/Person.svelte";
import Star from "../../svg/material/Star.svelte";
import RespondentSidebarItem from "./RespondentSidebarItem.svelte";

let title = $state("Test title");
let subtitle = $state("Test subtitle");
let icon = $state(Person);
let editable = $state(false);
let updateSubtitle = $state((newVal: string) => alert(`Updating to ${newVal}`));

export default {
  name: "RespondentSidebarItem",
  component: RespondentSidebarItem,
  category: "Respondent Detail",
  props: [
    {
      name: "title",
      value: title,
      type: "text",
    },
    {
      name: "subtitle",
      value: subtitle,
      type: "text",
    },
    {
      name: "icon",
      value: icon,
      type: "select",
      options: [
        { value: Person, label: "Person" },
        { value: Star, label: "Star" },
      ],
    },
    {
      name: "editable",
      value: editable,
      type: "bool",
    },
    {
      name: "updateSubtitle",
      value: updateSubtitle,
      type: "func",
      schema: `(newVal: string) => void`,
    },
  ],
  stories: [],
};
