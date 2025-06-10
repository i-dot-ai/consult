import { html } from 'lit';

import IaiResponseDashboard from './iai-response-dashboard.lit.csr.mjs';

const mockFetch = () => 
  Promise.resolve({
    ok: true,
    status: 200,
    json: () => Promise.resolve({
      "all_respondents": [],
      "has_more_pages": false,
      "respondents_total": 0,
      "filtered_total": 0
    })
  })

const TEST_STANCE_OPTIONS = [
  {
    name: "stances",
    inputId: "stance-one-input",
    label: "Stance One",
    value: "stance-one",
  },
  {
    name: "stances",
    inputId: "stance-two-input",
    label: "Stance Two",
    value: "stance-two",
  }
];

const TEST_THEME_MAPPIINGS = [
  {

    label: "Test Theme 1",
    description: "This is theme 1",
    count: 10,
    value: "theme-one",
    inputId: "theme-one",
  },
  {
    label: "Test Theme 2",
    description: "This is theme 2",
    count: 20,
    value: "theme-two",
    inputId: "theme-two",
  },
  {
    label: "Test Theme 3",
    description: "This is theme 3",
    count: 30,
    value: "theme-three",
    inputId: "theme-three",
  }
];

const TEST_MULTI_CHOICE = [
  {"Answer 1": 10},
  {"Answer 2": 20},
];

// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/ResponsesDashboard/ResponseDashboard',
  tags: ['autodocs'],
  render: (args) => {
    return html`
      <iai-response-dashboard
        .consultationTitle=${args.consultationTitle}
        .consultationSlug=${args.consultationTitle}
        .questionTitle=${args.questionTitle}
        .questionText=${args.questionText}
        .questionSlug=${args.questionSlug}
        .stanceOptions=${args.stanceOptions}
        .themeMappings=${args.themeMappings}
        .responses=${args.responses}
        .responsesTotal=${args.responsesTotal}
        .responsesFilteredTotal=${args.responsesFilteredTotal}
        .free_text_question_part=${args.free_text_question_part}
        .has_individual_data=${args.has_individual_data}
        .has_multiple_choice_question_part=${args.has_multiple_choice_question_part}
        .multiple_choice_summary=${args.multiple_choice_summary}
        .fetchData=${mockFetch}
      ></iai-response-dashboard>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Default = {
  args: {
    consultationTitle: "Test Consultation",
    consultationSlug: "test-consultation",
    questionTitle: "Test Question",
    questionText: "This is a text question".repeat(15),
    questionSlug: "test-question",
    stanceOptions: TEST_STANCE_OPTIONS,
    themeMappings: TEST_THEME_MAPPIINGS,
    responses: [],
    responsesTotal: 100,
    responsesFilteredTotal: 100,
    free_text_question_part: true,
    has_individual_data: true,
    has_multiple_choice_question_part: true,
    multiple_choice_summary: TEST_MULTI_CHOICE,
  },
};
