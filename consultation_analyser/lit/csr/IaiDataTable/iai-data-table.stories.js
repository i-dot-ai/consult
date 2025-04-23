import { html } from 'lit';
import { unsafeHTML } from 'lit/directives/unsafe-html.js';

import IaiDataTable from './iai-data-table.lit.csr.mjs';


const DEFAULT_DATA = [
  {
    "Theme name": "All Themes",
    "Total mentions": 104,
    "Positive mentions": 33,
    "Negative mentions": 48,
    _bottomRow: true,
  },
  {
    "Theme name": "Ban on Remote Prescribing",
    "Total mentions": 10,
    "Positive mentions": 3,
    "Negative mentions": 3,
  },
  {
    "Theme name": "Ban on Remote Prescribing",
    "Total mentions": 5,
    "Positive mentions": 3,
    "Negative mentions": 3,
  },
  {
    "Theme name": "Ban on Remote Prescribing",
    "Total mentions": 200,
    "Positive mentions": 3,
    "Negative mentions": 3,
  },
  {
    "Theme name": "Consistency in Regulations and Standards",
    "Total mentions": 1,
    "Positive mentions": 0,
    "Negative mentions": 1,
  },
];


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Example/IaiDataTable',
  tags: ['autodocs'],
  render: (args) => {
    return html`
      <iai-data-table
        .data=${args.data}
      ></iai-data-table>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args

export const DefaultTable = {
  args: {
    data: DEFAULT_DATA,
  }
};

export const TableWithRawHtml = {
  args: {
    data: [
      ...DEFAULT_DATA.slice(1),
      {
        ...DEFAULT_DATA[0],
        "Theme name": unsafeHTML(`<span style=\"color: red;\">All Themes</span>`)
      }
    ],
  }
};