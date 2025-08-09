export const getEnv = (url: string): string => {
    if (url.includes("consult-dev.ai.cabinetoffice.gov.uk")) {
        return "dev";
    }
    if (url.includes("consult.ai.cabinetoffice.gov.uk")) {
        return "prod";
    }
    return "local";
}

export const getBackendUrl = (url: string): string => {
    const backendUrl = import.meta.env.PUBLIC_BACKEND_URL;
    if (!backendUrl) {
        throw new Error("PUBLIC_BACKEND_URL environment variable is not set. This is required for the application to function.");
    }
    return backendUrl;
}

export const applyHighlight = (fullText: string, matchedText: string): string => {
    if (!matchedText) {
        return fullText;
    }
    const regex = new RegExp(matchedText, "gi");
    return fullText.replace(regex, match => `<span class="bg-yellow-300">${match}</span>`);
}