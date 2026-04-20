import { type Component } from "svelte";

import type { Mock } from "../../global/types";

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
import IntroCardStory from "../data/IntroCard/IntroCardStory.svelte";
import LearningsStory from "../data/Learnings/LearningsStory.svelte";
import IntroPageStory from "../data/IntroPage/IntroPageStory.svelte";
import StepOneAPageStory from "../data/StepOneAPage/StepOneAPageStory.svelte";
import StepOneBPageStory from "../data/StepOneBPage/StepOneBPageStory.svelte";
import ConsultationListStory from "../screens/ConsultationList/ConsultationListStory.svelte";
import ConsultationDetailStory from "../screens/ConsultationDetail/ConsultationDetailStory.svelte";
import FileVerifiedStory from "../data/FileVerified/FileVerifiedStory.svelte";
import StepsTitleStory from "../data/StepsTitle/StepsTitleStory.svelte";
import FileInputStory from "../inputs/FileInput/FileInputStory.svelte";
import CreateConsultationFormStory from "../screens/CreateConsultationForm/CreateConsultationFormStory.svelte";
import EditUserStory from "../screens/EditUserForm/EditUserStory.svelte";
import ConsultationAnalysisStory from "../screens/ConsultationAnalysis/ConsultationAnalysisStory.svelte";
import ThemeSignOffDetailCompletedStory from "../screens/ThemeSignOffDetailCompleted/ThemeSignOffDetailCompletedStory.svelte";
import AddUserFormStory from "../screens/AddUserForm/AddUserFormStory.svelte";

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
  mocks?: Mock[];
}
interface Story {
  name: string;
  component: Component;
  category?: string;
  props: StoryProp[];
  stories: StoryConfig[];
  mocks?: Mock[];
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
  IntroCardStory,
  LearningsStory,
  IntroPageStory,
  StepOneAPageStory,
  StepOneBPageStory,
  ConsultationListStory,
  ConsultationDetailStory,
  FileVerifiedStory,
  StepsTitleStory,
  FileInputStory,
  CreateConsultationFormStory,
  EditUserStory,
  ConsultationAnalysisStory,
  ThemeSignOffDetailCompletedStory,
  AddUserFormStory,
] as Story[];
