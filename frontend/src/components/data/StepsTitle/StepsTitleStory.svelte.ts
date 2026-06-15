import StepsTitle from "./StepsTitle.svelte";
import { TEST_DATA } from "./testData";

const text = $state(TEST_DATA.text);
const currentStep = $state(TEST_DATA.currentStep);
const totalSteps = $state(TEST_DATA.totalSteps);
const Icon = $state(TEST_DATA.Icon);

export default {
  name: "StepsTitle",
  component: StepsTitle,
  category: "Data",
  props: [
    { name: "text", value: text, type: "text" },
    { name: "currentStep", value: currentStep, type: "number" },
    { name: "totalSteps", value: totalSteps, type: "number" },
    { name: "Icon", value: Icon },
  ],
  stories: [
    {
      name: "Zero Steps",
      props: {
        ...TEST_DATA,
        totalSteps: 0,
        currentStep: 0,
      },
    },
    {
      name: "Many Steps",
      props: {
        ...TEST_DATA,
        totalSteps: 100,
      },
    },
    {
      name: "Last Step",
      props: {
        ...TEST_DATA,
        currentStep: 5,
        totalSteps: 5,
      },
    },
    {
      name: "First Step",
      props: {
        ...TEST_DATA,
        currentStep: 1,
        totalSteps: 5,
      },
    },
    {
      name: "Single Step",
      props: {
        ...TEST_DATA,
        currentStep: 1,
        totalSteps: 1,
      },
    },
  ],
};
