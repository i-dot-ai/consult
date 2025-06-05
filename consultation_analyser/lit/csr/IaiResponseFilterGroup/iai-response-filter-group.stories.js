import { html } from 'lit';

import { unsafeHTML } from 'lit/directives/unsafe-html.js';

import IaiResponseFilterGroup from './iai-response-filter-group.lit.csr.mjs';

// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/ResponseFilterGroup',
  tags: ['autodocs'],
  render: (args) => {
    return html`
      <iai-response-filter-group>
        <div slot="content">
          ${unsafeHTML(args.content)}
        </div>
      </iai-response-filter-group>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Default = {
  args: {
    title: "Test Title",
    content: `
      <ul>
        <li>Content 1</li>
        <li>Content 2</li>
      </ul>
    `,
  },
};

export const WithInput = {
  args: {
    title: "Test Title",
    content: `
      <div slot="content">
        <div>
          <div class="input-container">
            <iai-text-input
              inputId="responses-search-input"
              name="responses-search"
              label="Search"
              placeholder="Search..."
              value="test value"
            ></iai-text-input>
        </div>
      </div>
    `,
  },
};

