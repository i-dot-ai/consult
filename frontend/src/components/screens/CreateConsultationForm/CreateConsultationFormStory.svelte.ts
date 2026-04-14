// import { defaultMock, emptyMock, longMock } from "./mocks";

import { Routes } from "../../../global/routes";
import CreateConsultationForm from "./CreateConsultationForm.svelte";

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
  props: [],
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
