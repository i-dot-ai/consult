export enum Routes {
    Home = "/",
    Consultations = "/consultations",
    Support = "/support",
    SignOut = "/sign-out",
}

export const getConsultationDetailUrl = (consultationId: string) => {
    return `/${Routes.Consultations}/${consultationId}`;
};

export const getResponseDetailUrl = (consultationId: string, responseId: string) => {
    return `/${Routes.Consultations}/${consultationId}/responses/${responseId}`;
};