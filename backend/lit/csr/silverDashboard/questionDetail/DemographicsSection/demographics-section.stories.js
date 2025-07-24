import { html } from 'lit';

import { action } from "@storybook/addon-actions";

import DemographicsSection from './demographics-section.lit.csr.mjs';


const TEST_DATA = {
  categoryOne: {
    title: "Respondent type",
    data: {
      "Individual": 4340,
      "Organisation": 2660,
    }
  },
  categoryTwo: {
    title: "Geographic Distribution",
    data: {
      "England": 4900,
      "Scotland": 1120,
      "Wales": 700,
      "N. Ireland": 280
    }
  },
  categoryThree: {
    title: "Third Panel",
    data: {
      "England": 5000,
      "Scotland": 2120,
      "Wales": 300,
      "N. Ireland": 180
    }
  },
}

// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/SilverDashboard/QuestionDetail/DemographicsSection',
  tags: ['autodocs'],
  render: (args) => {
    return html`
      <iai-demographics-section
        .data=${args.data}
      ></iai-demographics-section>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const ThreeCategories = {
  args: {
    data: [
      TEST_DATA.categoryOne,
      TEST_DATA.categoryTwo,
      TEST_DATA.categoryThree,
    ]
  },
};


export const TwoCategories = {
  args: {
    data: [
      TEST_DATA.categoryOne,
      TEST_DATA.categoryTwo,
    ]
  },
};

export const OneCategory = {
  args: {
    data: [
      TEST_DATA.categoryOne,
    ]
  },
};