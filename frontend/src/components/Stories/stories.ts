import { type Component } from "svelte";

import ProgressStory from "../Progress/ProgressStory.svelte";
import HeaderStory from "../Header/HeaderStory.svelte";
import FooterStory from "../Footer/FooterStory.svelte";
import AccordionStory from "../Accordion/AccordionStory.svelte";
import PanelStory from "../dashboard/Panel/PanelStory.svelte";
import DemoFilterStory from "../DemoFilter/DemoFilterStory.svelte";
import RespondentSidebarItemStory from "../dashboard/RespondentSidebarItem/RespondentSidebarItemStory.svelte";
import ThemeFormStory from "../theme-sign-off/ThemeForm/ThemeFormStory.svelte";
import SelectedThemeCardStory from "../theme-sign-off/SelectedThemeCard/SelectedThemeCardStory.svelte";
import AnswersListStory from "../theme-sign-off/AnswersList/AnswersListStory.svelte";
import GeneratedThemeCardStory from "../theme-sign-off/GeneratedThemeCard/GeneratedThemeCardStory.svelte";
import ThemeSignoffDetailStory from "../screens/ThemeSignOffDetailStory.svelte";
import ThemeSignOffArchiveStory from "../screens/ThemeSignOffArchive/ThemeSignOffArchiveStory.svelte";

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
  ThemeFormStory,
  SelectedThemeCardStory,
  AnswersListStory,
  GeneratedThemeCardStory,
  ThemeSignoffDetailStory,
  ThemeSignOffArchiveStory,
] as Story[];
