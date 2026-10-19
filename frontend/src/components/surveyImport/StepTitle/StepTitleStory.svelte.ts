import Description from "../../svg/material/Description.svelte";
import Download from "../../svg/material/Download.svelte";
import Upload from "../../svg/material/Upload.svelte";
import StepTitle from "./StepTitle.svelte";

import { TEST_DATA } from "./testData";

const stepNo = $state(TEST_DATA.stepNo);
const maxStepNo = $state(TEST_DATA.maxStepNo);
const title = $state(TEST_DATA.title);
const isExternal = $state(TEST_DATA.isExternal);
const Icon = $state(TEST_DATA.Icon);

export default {
  name: "StepTitle",
  component: StepTitle,
  category: "Survey Import",
  props: [
    { name: "stepNo", value: stepNo, type: "number" },
    { name: "maxStepNo", value: maxStepNo, type: "number" },
    { name: "title", value: title, type: "text" },
    { name: "isExternal", value: isExternal, type: "bool" },
    {
      name: "Icon",
      value: Icon,
      type: "select",
      options: [
        {
          value: Upload,
          label: "Upload",
        },
        {
          value: Description,
          label: "Document",
        },
        {
          value: Download,
          label: "Download",
        },
      ],
    },
  ],
  stories: [],
};
