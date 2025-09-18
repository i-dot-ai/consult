export interface NavItem {
    text: string;
    url: string;
}

export interface QuestionMultiAnswer {
    id: string;
    text: string;
    response_count: number;
}

export interface Question {
    id?: string;
    number?: number;
    total_responses?: number;
    question_text?: string;
    slug?: string;
    has_free_text?: boolean;
    has_multiple_choice?: boolean;
    multiple_choice_answer?: QuestionMultiAnswer[];
    proportion_of_audited_answers?: number;
}

export interface Consultation {
    title: string;
    id: string;
    slug: string;
    questions: Question[];
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
    demographic_data: { [category: string]: string };
    themes: ResponseTheme[];
    multiple_choice_answer: string[];
    evidenceRich: boolean;
    sentiment: string;
    human_reviewed: boolean;
    is_flagged: boolean;
    is_edited?: boolean;
}

export interface DemoOption {
    [category: string]: string[];
}

export interface DemoData {
    [category: string]: { [rowKey: string]: number };
}

export interface DemoTotalCounts {
    [category: string]: number;
}
export interface ThemeAggr {
    [id: string]: number;
}

export interface ConsultationResponse {
    id: string;
    title: string;
    slug: string;
    questions: Question[];
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

export interface DemoAggrResponse {
    demographic_aggregations: DemoData;
}

export interface ThemeAggrResponse {
    theme_aggregations: ThemeAggr;
}

export interface MultiChoiceResponseItem {
    answer: string;
    response_count: number;
}
export type MultiChoiceResponse = MultiChoiceResponseItem[];

export interface DemoOptionsResponseItem {
    name: string;
    value: string;
    count: number;
}
export type DemoOptionsResponse = DemoOptionsResponseItem[];