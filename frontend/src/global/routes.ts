export enum Routes {
  Home = "/",
  Evaluations = "/evaluations",
  Consultations = "/consultations",
  Support = "/support",
  HowItWorks = "/how-it-works",
  DataSharing = "/data-sharing",
  GetInvolved = "/get-involved",
  SignIn = "/sign-in",
  SignOut = "/sign-out",
  ApiMagicLink = "/api/magic-link/",
  ApiConsultations = "/api/consultations",
  ApiConsultationFolders = "/api/consultation-folders",
  ApiConsultationImport = "/api/consultation-import",
  ApiUser = "/api/user/",
  ApiAstroSignIn = "/api/astro/sign-in",
  Design = "/design",
  SupportImport = "/support/consultations/import-summary",
  ImportConsultations = "/support/consultations/import-consultation",
  SupportUsers = "/support/users",
  SupportConsultations = "/support/consultations",
  SupportSignOff = "/support/consultations/sign-off",
  SupportThemefinder = "/support/consultations/themefinder",
  SupportEmail = "consult@cabinetoffice.gov.uk",
  SupportQueue = "/support/django-rq",
}
export const getConsultationDetailUrl = (consultationId: string) => {
  return `${Routes.Consultations}/${consultationId}`;
};
export const getConsultationAnalysisUrl = (consultationId: string) => {
  return `${Routes.Consultations}/${consultationId}/analysis/`;
};

export const getThemeSignOffUrl = (consultationId: string) => {
  return `${Routes.Consultations}/${consultationId}/theme-sign-off`;
};
export const getThemeSignOffDetailUrl = (
  consultationId: string,
  questionId: string,
) => {
  return `${Routes.Consultations}/${consultationId}/theme-sign-off/${questionId}`;
};

export const getConsultationEvalUrl = (consultationId: string) => {
  return `${Routes.Evaluations}/${consultationId}/questions/`;
};

export const getQuestionDetailUrl = (
  consultationId: string,
  questionId: string,
) => {
  if (!consultationId || !questionId) {
    return "#";
  }
  return `${Routes.Consultations}/${consultationId}/responses/${questionId}`;
};

export const getRespondentDetailUrl = (
  consultationId: string,
  respondentId: string,
) => {
  if (!consultationId || !respondentId) {
    return "#";
  }
  return `${Routes.Consultations}/${consultationId}/respondent/${respondentId}`;
};
export const getApiConsultationUrl = (consultationId: string) => {
  return `${Routes.ApiConsultations}/${consultationId}/`;
};
export const getApiAnswersUrl = (consultationId: string) => {
  return `/api/consultations/${consultationId}/responses/`;
};
export const getApiQuestionsUrl = (consultationId: string) => {
  return `${Routes.ApiConsultations}/${consultationId}/questions/`;
};
export const getApiQuestionUrl = (
  consultationId: string,
  questionId: string,
) => {
  return `${Routes.ApiConsultations}/${consultationId}/questions/${questionId}`;
};
export const getApiAnswerUrl = (
  consultationId: string,
  questionId: string,
  answerId: string,
) => {
  return `${Routes.ApiConsultations}/${consultationId}/responses/${answerId}/`;
};
export const getApiAnswerFlagUrl = (
  consultationId: string,
  questionId: string,
  answerId: string,
) => {
  return `${Routes.ApiConsultations}/${consultationId}/responses/${answerId}/toggle-flag/`;
};
export const getApiConsultationRespondentsUrl = (consultationId: string) => {
  return `${Routes.ApiConsultations}/${consultationId}/respondents/`;
};
export const getApiConsultationRespondentUrl = (
  consultationId: string,
  respondentId: string,
) => {
  return `${Routes.ApiConsultations}/${consultationId}/respondents/${respondentId}/`;
};
export const getQuestionsByRespondentUrl = (
  consultationId: string,
  respondentId: string,
) => {
  return `${Routes.ApiConsultations}/${consultationId}/questions/?respondent_id=${respondentId}`;
};

export const getApiGetSelectedThemesUrl = (
  consultationId: string,
  questionId: string,
) => {
  return `${Routes.ApiConsultations}/${consultationId}/questions/${questionId}/selected-themes/`;
};
export const getApiDeleteSelectedThemeUrl = (
  consultationId: string,
  questionId: string,
  themeId: string,
) => {
  return `${Routes.ApiConsultations}/${consultationId}/questions/${questionId}/selected-themes/${themeId}/`;
};
export const getApiUpdateSelectedThemeUrl = (
  consultationId: string,
  questionId: string,
  themeId: string,
) => {
  return `${Routes.ApiConsultations}/${consultationId}/questions/${questionId}/selected-themes/${themeId}/`;
};
export const getApiCreateSelectedThemeUrl = (
  consultationId: string,
  questionId: string,
) => {
  return `${Routes.ApiConsultations}/${consultationId}/questions/${questionId}/selected-themes/`;
};
export const getApiGetGeneratedThemesUrl = (
  consultationId: string,
  questionId: string,
) => {
  return `${Routes.ApiConsultations}/${consultationId}/questions/${questionId}/candidate-themes/`;
};
export const getApiSelectGeneratedThemeUrl = (
  consultationId: string,
  questionId: string,
  themeId: string,
) => {
  return `${Routes.ApiConsultations}/${consultationId}/questions/${questionId}/candidate-themes/${themeId}/select/`;
};
export const getApiConfirmSignOffUrl = (
  consultationId: string,
  questionId: string,
) => {
  return `${Routes.ApiConsultations}/${consultationId}/questions/${questionId}/`;
};

export const getApiShowNextResponse = (
  consultationId: string,
  questionId: string,
) => {
  return `${Routes.Evaluations}/${consultationId}/questions/${questionId}/show-next`;
};
