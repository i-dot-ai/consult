interface ConsultationResponseQuestion {
    id: string;
    title: string;
    url: string;
    numResponses: Number;
    status: "Open";
}

interface ConsultationResponse {
    title: string;
    questions: Array<ConsultationResponseQuestion>;
}

export const getConsultationById = (consultationId: string): ConsultationResponse => {
    // TODO: Implement fetching from endpoint

    const mockData: ConsultationResponse = {
        title: "Mock Consultation",
        questions: [
            {
                id: "1",
                title: "Q1: Mock Question 1",
                url: `/consultations/${consultationId}/responses/${1}`,
                numResponses: 203,
                status: "Open",
            },
            {
                id: "2",
                title: "Q2: Mock Question 2",
                url: `/consultations/${consultationId}/responses/${2}`,
                numResponses: 405,
                status: "Open",
            },
        ]
    };
    return mockData;
};