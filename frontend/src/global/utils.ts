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

export const applyHighlight = (fullText: string, matchedText: string): string => {
    if (!matchedText) {
        return fullText;
    }
    const regex = new RegExp(matchedText, "gi");
    return fullText.replace(regex, match => `<span class="bg-yellow-300">${match}</span>`);
}

export const getPercentage = (partialValue: number, totalValue: number): number => {
    if (totalValue === 0) {
        return 0;
    }
    const percentage = (partialValue / totalValue) * 100;

    // Round to 1 decimal point
    return Math.round(percentage * 10) / 10;
}