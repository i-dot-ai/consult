import urlJoin from "url-join";

export enum Suffixes {
  ThemeSignOff = "theme-sign-off",
  Analysis = "analysis",
  Consultations = "consultations",
  Questions = "questions",
  Responses = "responses",
  Respondent = "respondent",
  Respondents = "respondents",
  ToggleFlag = "toggle-flag",
  MarkRead = "mark-read",
  Themes = "themes",
  Users = "users",
  AddUsers = "add-users",
  SelectedThemes = "selected-themes",
  CandidateThemes = "candidate-themes",
  Select = "select",
  ShowNext = "show-next",
}

export enum Routes {
  Home = "/",
  Evaluations = "/evaluations",
  Consultations = "/consultations",
  Support = "/support",
  HowItWorks = "/how-it-works",
  DataSharing = "/data-sharing",
  GetInvolved = "/get-involved",
  SignInError = "/sign-in-error",
  APIValidateToken = "/api/validate-token/",
  ApiResponses = "/api/responses/",
  ApiConsultations = "/api/consultations/",
  ApiConsultationFolders = "/api/consultations/folders/",
  ApiConsultationImport = "/api/consultations/import/",
  ApiConsultationImportImmutable = "/api/consultations/import-immutable/",
  ApiConsultationImportCandidateThemes = "/api/consultations/import-candidate-themes/",
  ApiConsultationImportAnnotations = "/api/consultations/import-annotations/",
  ApiConsultationExport = "/api/consultations/export/",
  ApiConsultationQuestions = "/api/questions/",
  ApiUser = "/api/user/",
  ApiUsers = "/api/users/",
  ApiAstroSignIn = "/api/astro/sign-in/",
  Design = "/design",
  SupportImport = "/support/consultations/import-summary",
  ImportConsultations = "/support/consultations/import-consultation",
  SupportUsers = "/support/users",
  SupportConsultations = "/support/consultations",
  SupportSignOff = "/support/consultations/sign-off",
  SupportThemefinder = "/support/consultations/themefinder",
  SupportEmail = "consult@cabinetoffice.gov.uk",
  SupportQueue = "/support/django-rq",
  Profile = "/profile",
  Privacy = "/privacy",
  Guidance = "/guidance",
}

export const getConsultationDetailUrl = (consultationId: string) => {
  return urlJoin(Routes.Consultations, consultationId);
};
export const getConsultationAnalysisUrl = (consultationId: string) => {
  return urlJoin(Routes.Consultations, consultationId, Suffixes.Analysis, "/");
};

export const getThemeSignOffUrl = (consultationId: string) => {
  return urlJoin(Routes.Consultations, consultationId, Suffixes.ThemeSignOff);
};
export const getThemeSignOffDetailUrl = (
  consultationId: string,
  questionId: string,
) => {
  return urlJoin(
    Routes.Consultations,
    consultationId,
    Suffixes.ThemeSignOff,
    questionId,
  );
};

export const getConsultationEvalUrl = (consultationId: string) => {
  return urlJoin(Routes.Evaluations, consultationId, Suffixes.Questions, "/");
};

export const getQuestionDetailUrl = (
  consultationId: string,
  questionId: string,
) => {
  if (!consultationId || !questionId) {
    return "#";
  }
  return urlJoin(
    Routes.Consultations,
    consultationId,
    Suffixes.Responses,
    questionId,
  );
};

export const getRespondentDetailUrl = (
  consultationId: string,
  respondentId: string,
) => {
  if (!consultationId || !respondentId) {
    return "#";
  }
  return urlJoin(
    Routes.Consultations,
    consultationId,
    Suffixes.Respondent,
    respondentId,
  );
};
export const getApiConsultationUrl = (consultationId: string) => {
  return urlJoin(Routes.ApiConsultations, consultationId, "/");
};
export const getApiAnswersUrl = (consultationId: string) => {
  return urlJoin(
    Routes.ApiConsultations,
    consultationId,
    Suffixes.Responses,
    "/",
  );
};
export const getApiQuestionsUrl = (consultationId: string) => {
  return urlJoin(
    Routes.ApiConsultations,
    consultationId,
    Suffixes.Questions,
    "/",
  );
};
export const getApiQuestionUrl = (
  consultationId: string,
  questionId: string,
) => {
  return urlJoin(
    Routes.ApiConsultations,
    consultationId,
    Suffixes.Questions,
    questionId,
    "/",
  );
};
export const getApiAnswerUrl = (consultationId: string, answerId: string) => {
  return urlJoin(
    Routes.ApiConsultations,
    consultationId,
    Suffixes.Responses,
    answerId,
    "/",
  );
};
export const getApiAnswerFlagUrl = (
  consultationId: string,
  answerId: string,
) => {
  return urlJoin(
    Routes.ApiConsultations,
    consultationId,
    Suffixes.Responses,
    answerId,
    Suffixes.ToggleFlag,
    "/",
  );
};
export const getApiConsultationRespondentsUrl = (consultationId: string) => {
  return urlJoin(
    Routes.ApiConsultations,
    consultationId,
    Suffixes.Respondents,
    "/",
  );
};
export const getApiConsultationRespondentUrl = (
  consultationId: string,
  respondentId: string,
) => {
  return urlJoin(
    Routes.ApiConsultations,
    consultationId,
    Suffixes.Respondents,
    respondentId,
    "/",
  );
};
export const getQuestionsByRespondentUrl = (
  consultationId: string,
  respondentId: string,
) => {
  return urlJoin(
    Routes.ApiConsultations,
    consultationId,
    Suffixes.Questions,
    `?respondent_id=${respondentId}`,
  );
};

export const getApiGetSelectedThemesUrl = (
  consultationId: string,
  questionId: string,
) => {
  return urlJoin(
    Routes.ApiConsultations,
    consultationId,
    Suffixes.Questions,
    questionId,
    Suffixes.SelectedThemes,
    "/",
  );
};
export const getApiDeleteSelectedThemeUrl = (
  consultationId: string,
  questionId: string,
  themeId: string,
) => {
  return urlJoin(
    Routes.ApiConsultations,
    consultationId,
    Suffixes.Questions,
    questionId,
    Suffixes.SelectedThemes,
    themeId,
    "/",
  );
};
export const getApiUpdateSelectedThemeUrl = (
  consultationId: string,
  questionId: string,
  themeId: string,
) => {
  return urlJoin(
    Routes.ApiConsultations,
    consultationId,
    Suffixes.Questions,
    questionId,
    Suffixes.SelectedThemes,
    themeId,
    "/",
  );
};
export const getApiCreateSelectedThemeUrl = (
  consultationId: string,
  questionId: string,
) => {
  return urlJoin(
    Routes.ApiConsultations,
    consultationId,
    Suffixes.Questions,
    questionId,
    Suffixes.SelectedThemes,
    "/",
  );
};
export const getApiGetGeneratedThemesUrl = (
  consultationId: string,
  questionId: string,
) => {
  return urlJoin(
    Routes.ApiConsultations,
    consultationId,
    Suffixes.Questions,
    questionId,
    Suffixes.CandidateThemes,
    "/",
  );
};
export const getApiSelectGeneratedThemeUrl = (
  consultationId: string,
  questionId: string,
  themeId: string,
) => {
  return urlJoin(
    Routes.ApiConsultations,
    consultationId,
    Suffixes.Questions,
    questionId,
    Suffixes.CandidateThemes,
    themeId,
    Suffixes.Select,
    "/",
  );
};
export const getApiConfirmSignOffUrl = (
  consultationId: string,
  questionId: string,
) => {
  return urlJoin(
    Routes.ApiConsultations,
    consultationId,
    Suffixes.Questions,
    questionId,
    "/",
  );
};

export const getApiShowNextResponse = (
  consultationId: string,
  questionId: string,
) => {
  return urlJoin(
    Routes.ApiConsultations,
    consultationId,
    Suffixes.Questions,
    questionId,
    Suffixes.ShowNext,
    "/",
  );
};

export const getResponseDetailUrl = (
  consultationId: string,
  questionId: string,
  responseId: string,
) => {
  return urlJoin(
    Routes.Evaluations,
    consultationId,
    Suffixes.Questions,
    questionId,
    Suffixes.Responses,
    responseId,
    "/",
  );
};

export const updateResponseReadStatus = (
  consultationId: string,
  responseId: string,
) => {
  return urlJoin(
    Routes.ApiConsultations,
    consultationId,
    Suffixes.Responses,
    responseId,
    Suffixes.MarkRead,
    "/",
  );
};

export const getApiQuestionResponse = (
  consultationId: string,
  questionId: string,
  responseId: string,
) => {
  return urlJoin(
    Routes.ApiConsultations,
    consultationId,
    Suffixes.Responses,
    responseId,
    "/",
  );
};

export const getThemeInformationResponse = (
  consultationId: string,
  questionId: string,
  responseId: string,
) => {
  return urlJoin(
    Routes.ApiConsultations,
    consultationId,
    Suffixes.Responses,
    responseId,
    Suffixes.Themes,
  );
};

export const getApiAddUserToConsultation = (consultationId: string) => {
  return urlJoin(
    Routes.ApiConsultations,
    consultationId,
    Suffixes.AddUsers,
    "/",
  );
};

export const getApiRemoveUserFromConsultation = (
  consultationId: string,
  userId: string,
) => {
  return urlJoin(
    Routes.ApiConsultations,
    consultationId,
    Suffixes.Users,
    userId,
    "/",
  );
};

export const getApiUserDetails = (userId: string) => {
  return urlJoin(Routes.ApiUsers, userId, "/");
};

export const getSupportConsultationDetails = (consultationId: string) => {
  return urlJoin(Routes.SupportConsultations, consultationId);
};

export const getApiUserConsultations = (userId: string) => {
  return urlJoin(Routes.ApiUsers, userId, "consultations/");
};
