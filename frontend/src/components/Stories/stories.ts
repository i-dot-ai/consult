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
import NavigationHeaderStory from "../navigation/Header/HeaderStory.svelte";
import HeaderConsultStory from "../navigation/HeaderConsult/HeaderConsultStory.svelte";
import BreadcrumbsStory from "../navigation/Breadcrumbs/BreadcrumbsStory.svelte";
import ProfileButtonStory from "../navigation/ProfileButton/ProfileButtonStory.svelte";
import FloatingPanelStory from "../navigation/FloatingPanel/FloatingPanelStory.svelte";
import ChecklistStory from "../data/Checklist/ChecklistStory.svelte";

interface StoryProp {
  name: string;
  value: unknown;
  type: "number" | "text" | "bool" | "select" | "json" | "html" | "func";
  schema?: string;
  rawHtml?: string;
  label?: string;
  options?: {
    label: string;
    value: unknown;
  }[];
}
interface StoryConfig {
  name: string;
  props?: unknown;
}
interface Story {
  name: string;
  component: Component;
  category?: string;
  props: StoryProp[];
  stories: StoryConfig[];
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
  NavigationHeaderStory,
  HeaderConsultStory,
  BreadcrumbsStory,
  ProfileButtonStory,
  FloatingPanelStory,
  ChecklistStory,
] as Story[];
