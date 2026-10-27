import {
  getApiConsultationDeepValidationUrl,
  getApiConsultationUploadUrl,
} from "../../../../global/routes";

export const CONSULTATION_ID = "test-consultation";

const DEEP_VALIDATION_URL =
  getApiConsultationDeepValidationUrl(CONSULTATION_ID);
const UPLOAD_URL = getApiConsultationUploadUrl(CONSULTATION_ID);

export const deepValidationInvalidMock = {
  url: DEEP_VALIDATION_URL,
  method: "POST",
  body: {
    valid: false,
    rejection_type: "hard",
    message: "File failed deep validation with a hard rejection.",
    errors: [
      {
        code: "empty_responses",
        message: "The file does not contain a response row.",
      },
    ],
  },
};

export const deepValidationValidMock = {
  url: DEEP_VALIDATION_URL,
  method: "POST",
  body: {
    valid: true,
    rejection_type: null,
    message: "File passed deep validation.",
    errors: [],
    question_count: 2,
    response_count: 2,
    blank_cell_count: 0,
  },
};

export const uploadMock = {
  url: UPLOAD_URL,
  method: "POST",
};
