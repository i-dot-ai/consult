import { html } from 'lit';

import { unsafeHTML } from 'lit/directives/unsafe-html.js';

import IaiQuestionTopbar from './iai-question-topbar.lit.csr.mjs';


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/QuestionsArchive/QuestionTopbar',
  tags: ['autodocs'],
  render: (args) => {
    return html`
      <iai-question-topbar .title=${args.title}>
        <div slot="buttons">
          ${unsafeHTML(args.buttons)}
        </div>
      </iai-question-topbar>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Default = {
  args: {
    title: "Test Title",
    buttons: `
      <ul>
        <li>
          <button>Button 1</button>
        </li>
        <li>
          <button>Button 2</button>
        </li>
      </ul>
    `,
  },
};

export const LongTitle = {
  args: {
    title: "Test Title".repeat(10),
    buttons: `
      <ul>
        <li>
          <button>Button 1</button>
        </li>
        <li>
          <button>Button 2</button>
        </li>
      </ul>
    `,
  },
};

export const WithoutButtons = {
  args: {
    title: "Test Title",
  },
};
