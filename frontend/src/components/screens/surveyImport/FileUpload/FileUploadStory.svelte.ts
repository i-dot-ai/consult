import FileUpload from "./FileUpload.svelte";
import { CONSULTATION_ID, deepValidationInvalidMock, deepValidationValidMock, uploadMock } from "./mocks";

const consultationId = $state(CONSULTATION_ID);

export default {
  name: "FileUpload",
  component: FileUpload,
  category: "Screens / Survey Import",
  mocks: [ deepValidationValidMock, uploadMock ],
  props: [{ name: "consultationId", value: consultationId, type: "text" }],
  stories: [
    {
        name: "Validation Invalid",
        mocks: [deepValidationInvalidMock, uploadMock],
        props: { consultationId: consultationId },
    },
    {
        name: "Validation Valid",
        mocks: [deepValidationValidMock, uploadMock],
        props: { consultationId: consultationId },
    }
  ],
};
