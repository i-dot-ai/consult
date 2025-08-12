export enum Routes {
    Home = "/",
    Consultations = "/consultations",
    Support = "/support",
    HowItWorks = "/how-it-works",
    DataSharing = "/data-sharing",
    GetInvolved = "/get-involved",
    SignIn = "/sign-in",
    SignOut = "/sign-out",
    ApiConsultations = "/api/consultations",
    ApiUser = "/api/user/",
}
export const getConsultationDetailUrl = (consultationId: string) => {
    return `${Routes.Consultations}/${consultationId}`;
};

export const getConsultationEvalUrl = (consultationId: string) => {
    return `${Routes.Consultations}/${consultationId}/review-questions/`;
};

export const getQuestionDetailUrl = (consultationId: string, questionId: string) => {
    return `${Routes.Consultations}/${consultationId}/responses/${questionId}`;
};

export const getApiConsultationUrl = (consultationId: string) => {
    return `${Routes.ApiConsultations}/${consultationId}`;
}