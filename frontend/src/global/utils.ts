export const getEnv = (url: string): string => {
    if (url.includes("consult-dev.ai.cabinetoffice.gov.uk")) {
        return "dev";
    }
    if (url.includes("consult.ai.cabinetoffice.gov.uk")) {
        return "prod";
    }
    return "local";
}

export const getBackendUrl = (url: string): string | undefined => {
    const env = getEnv(url);

    if (env === "prod") {
        return "https://consult.ai.cabinetoffice.gov.uk";
    } else if (env === "dev") {
        return "https://consult-dev.ai.cabinetoffice.gov.uk";
    } else if (env === "local") {
        return "http://localhost:8000";
    }
}