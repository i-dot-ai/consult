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
  ApiConsultations = "/api/consultations",
  ApiUser = "/api/user/",
  ApiAstroSignIn = "/api/astro/sign-in",
  Design = "/design",
}
export const getConsultationDetailUrl = (consultationId: string) => {
  return `${Routes.Consultations}/${consultationId}`;
};
export const getConsultationAnalysisUrl = (consultationId: string) => {
  return `${Routes.Consultations}/${consultationId}/analysis/`;
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
  return `${Routes.ApiConsultations}/${consultationId}`;
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
