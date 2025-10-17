import { type Component } from "svelte";

import ProgressStory from "../Progress/ProgressStory.svelte";
import HeaderStory from "../Header/HeaderStory.svelte";
import FooterStory from "../Footer/FooterStory.svelte";
import AccordionStory from "../Accordion/AccordionStory.svelte";
import PanelStory from "../dashboard/Panel/PanelStory.svelte";
import DemoFilterStory from "../DemoFilter/DemoFilterStory.svelte";
import RespondentSidebarItemStory from "../dashboard/RespondentSidebarItem/RespondentSidebarItemStory.svelte";
import AddCustomThemeStory from "../theme-signoff/AddCustomTheme/AddCustomThemeStory.svelte";
import SelectedThemeCardStory from "../theme-signoff/SelectedThemeCard/SelectedThemeCardStory.svelte";
import AnswersListStory from "../theme-signoff/AnswersList/AnswersListStory.svelte";
import GeneratedThemeCardStory from "../theme-signoff/GeneratedThemeCard/GeneratedThemeCardStory.svelte";

interface StoryProp {
  name: string;
  value: any;
  type: "number" | "text" | "bool" | "select" | "json" | "html" | "func";
  schema?: string;
}
interface Story {
  name: string;
  component: Component;
  category?: string;
  props: StoryProp[];
  stories: any[];
}

export default [
  ProgressStory,
  HeaderStory,
  FooterStory,
  AccordionStory,
  PanelStory,
  DemoFilterStory,
  RespondentSidebarItemStory,
  AddCustomThemeStory,
  SelectedThemeCardStory,
  AnswersListStory,
  GeneratedThemeCardStory,
] as Story[];
