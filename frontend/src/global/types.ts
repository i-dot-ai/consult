export interface NavItem {
    text: string;
    url: string;
}

export interface Question {
    id: string;
    number: number;
    total_responses: number;
    question_text: string;
    slug: string;
    has_free_text: boolean;
    has_multiple_choice: boolean;
    multiple_choice_options: Array<any>;
}

export interface Consultation {
    title: string;
    id: string;
    slug: string;
    questions: Array<Question>;
}

export interface FormattedTheme {
    id: string;
    name: string;
    description: string;
    count: number;
    highlighted?: boolean;
    handleClick?: (e: MouseEvent) => void;
    key?: string;
}

export interface SelectOption {
    value: string;
    label: string;
}

export enum SearchModeValues {
    SEMANTIC = "semantic",
    KEYWORD = "keyword",
}
export enum SearchModeLabels {
    SEMANTIC = "Semantic",
    KEYWORD = "Keyword",
}
export enum TitleLevels {
    One = 1,
    Two = 2,
    Three = 3,
    Four = 4,
    Five = 5,
    Six = 6,
}

export enum TabNames {
    QuestionSummary = "tab-question-summary",
    ResponseAnalysis = "tab-response-analysis",
}

export enum TabDirections {
    Forward = "forward",
    Backward = "backward",
}

export interface SearchableSelectOption {
    value: any,
    label: string,
    description?: string,
    disabled?: boolean,
}

export interface ResponseTheme {
    id: string;
    name: string
    description: string;
    key?: string;
}

export interface ResponseAnswer {
    id: string;
    identifier: number;
    free_text_answer_text: string;
    demographic_data: Object;
    themes: ResponseTheme[];
    multiple_choice_answer: string[];
    evidenceRich: boolean;
    sentiment: string;
    human_reviewed: boolean;
    is_flagged: boolean;
}

export interface AnswersResponse {
    respondents_total: number;
    filtered_total: number;
    has_more_pages: boolean;
    all_respondents: ResponseAnswer[];
}
export interface ThemeInfoResponse {
    themes: ResponseTheme[];
}