import { html } from 'lit';
import { unsafeHTML } from 'lit/directives/unsafe-html.js';

import IaiDataTable from './iai-data-table.lit.csr.mjs';
import { DEFAULT_DATA } from './testData.mjs';


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

export const TableWithEncodedProps = {
  args: {
    data: DEFAULT_DATA,
  },

  render: (args) => {
    return html`
      <iai-data-table
        .encprops=${btoa(JSON.stringify({"data": args.data}))}
      ></iai-data-table>
    `
  },
};