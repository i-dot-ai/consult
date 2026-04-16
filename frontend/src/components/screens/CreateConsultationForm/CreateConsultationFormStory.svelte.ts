import CreateConsultationForm from "./CreateConsultationForm.svelte";
import { defaultMock } from "./mocks";

const s3Folders = $state(["folder-1", "folder-2"]);

export default {
  name: "CreateConsultationForm",
  component: CreateConsultationForm,
  category: "Screens",
  mocks: [
    defaultMock,
  ],
  props: [{ name: "s3Folders", value: s3Folders, type: "json" }],
  stories: [
    {
      name: "Success",
      mocks: [
        defaultMock,,
      ],
      props: { s3Folders },
    },
    {
      name: "4xx Error",
      mocks: [
        {
          ...defaultMock,
          status: 400,
          body: { message: "Bad request", status: 400 },
        },
      ],
      props: { s3Folders },
    },
    {
      name: "5xx Error",
      mocks: [
        {
          ...defaultMock,
          status: 500,
          body: { message: "Unexpected server error", status: 500 },
        },
      ],
      props: { s3Folders },
    },
    {
      name: "Fetch Error",
      mocks: [
        {
          ...defaultMock,
          throws: new Error("Fetch failed"),
        },
      ],
      props: { s3Folders },
    },
  ],
};
