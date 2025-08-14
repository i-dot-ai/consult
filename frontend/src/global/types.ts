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