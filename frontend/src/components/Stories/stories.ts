import { type Component } from "svelte";

import ProgressStory from "../Progress/ProgressStory.svelte";
import HeaderStory from "../Header/HeaderStory.svelte";
import FooterStory from "../Footer/FooterStory.svelte";
import AccordionStory from "../Accordion/AccordionStory.svelte";
import PanelStory from "../dashboard/Panel/PanelStory.svelte";
import DemoFilterStory from "../DemoFilter/DemoFilterStory.svelte";
import RespondentSidebarItemStory from "../dashboard/RespondentSidebarItem/RespondentSidebarItemStory.svelte";
import ThemeFormStory from "../theme-sign-off/question/selected-themes/ThemeForm/ThemeFormStory.svelte";
import SelectedThemeCardStory from "../theme-sign-off/question/selected-themes/SelectedThemeCard/SelectedThemeCardStory.svelte";
import RepresentativeResponsesStory from "../theme-sign-off/question/RepresentativeResponses/RepresentativeResponses.story.svelte";
import CandidateThemeCardStory from "../theme-sign-off/question/candidate-themes/CandidateThemeCard/CandidateThemeCard.story.svelte";
import SignOffEditorStory from "../theme-sign-off/question/SignOffEditor.story.svelte";
import NavigationHeaderStory from "../navigation/Header/HeaderStory.svelte";
import HeaderConsultStory from "../navigation/HeaderConsult/HeaderConsultStory.svelte";
import BreadcrumbsStory from "../navigation/Breadcrumbs/BreadcrumbsStory.svelte";
import ProfileButtonStory from "../navigation/ProfileButton/ProfileButtonStory.svelte";
import FloatingPanelStory from "../navigation/FloatingPanel/FloatingPanelStory.svelte";

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
  RepresentativeResponsesStory,
  CandidateThemeCardStory,
  SignOffEditorStory,
  NavigationHeaderStory,
  HeaderConsultStory,
  BreadcrumbsStory,
  ProfileButtonStory,
  FloatingPanelStory,
] as Story[];
