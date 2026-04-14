import { Routes } from "../../../global/routes";
import CreateConsultationForm from "./CreateConsultationForm.svelte";

const s3Folders = $state(["folder-1", "folder-2"]);

export default {
  name: "CreateConsultationForm",
  component: CreateConsultationForm,
  category: "Screens",
  mocks: [
    {
      url: Routes.ApiConsultationSetup,
      method: "POST",
    },
  ],
  props: [{ name: "s3Folders", value: s3Folders, type: "json" }],
  stories: [
    {
      name: "Success",
      mocks: [
        {
          url: Routes.ApiConsultationSetup,
          method: "POST",
        },
      ],
    },
    {
      name: "4xx Error",
      mocks: [
        {
          url: Routes.ApiConsultationSetup,
          method: "POST",
          status: 400,
          body: { message: "Bad request", status: 400 },
        },
      ],
    },
    {
      name: "5xx Error",
      mocks: [
        {
          url: Routes.ApiConsultationSetup,
          method: "POST",
          status: 500,
          body: { message: "Unexpected server error", status: 500 },
        },
      ],
    },
    {
      name: "Fetch Error",
      mocks: [
        {
          url: Routes.ApiConsultationSetup,
          method: "POST",
          throws: new Error("Fetch failed"),
        },
      ],
    },
  ],
};
