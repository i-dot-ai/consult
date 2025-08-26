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
    handleClick?: Function;
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