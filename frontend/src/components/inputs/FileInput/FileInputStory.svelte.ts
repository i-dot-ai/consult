import type { File } from "buffer";

import FileInput from "./FileInput.svelte";
import { TEST_DATA } from "./testData";

let id = $state(TEST_DATA.id);
let title = $state(TEST_DATA.title);
let subtitle = $state(TEST_DATA.subtitle);
let accept = $state(TEST_DATA.accept);
let maxSize = $state(TEST_DATA.maxSize);
let multiple = $state(TEST_DATA.multiple);
let onConfirm = $state((files: File[]) => console.log(files));

export default {
  name: "FileInput",
  component: FileInput,
  category: "Inputs",
  props: [
    { name: "id", value: id, type: "text" },
    { name: "title", value: title, type: "text" },
    { name: "subtitle", value: subtitle, type: "text" },
    { name: "accept", value: accept, type: "text" },
    { name: "maxSize", value: maxSize, type: "number" },
    { name: "multiple", value: multiple, type: "bool" },
    { name: "onConfirm", value: onConfirm, type: "func" },
  ],
  stories: [
    {
      name: "Default",
      props: { id: "file-input-default" },
    },
  ],
};
