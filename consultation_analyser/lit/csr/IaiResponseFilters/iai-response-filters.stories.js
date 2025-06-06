import { html } from 'lit';

import IaiResponseFilters from './iai-response-filters.lit.csr.mjs';
import { unsafeHTML } from 'lit/directives/unsafe-html.js';

// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/ResponsesDashboard/ResponseFilters',
  tags: ['autodocs'],
  render: (args) => {
    return html`
      <iai-response-filters>
        <div slot="filters">
          ${unsafeHTML(args.filters)}
        </div>
      </iai-response-filters>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Default = {
  args: {
    filters: `
      <ul>
        <li>Filter 1</li>
        <li>Filter 2</li>
      </ul>
    `,
  },
};