import { html } from 'lit';
import { unsafeHTML } from 'lit/directives/unsafe-html.js';

import { action } from "@storybook/addon-actions";

import IaiIconButton from './iai-icon-button.lit.csr.mjs';


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/IconButton',
  tags: ['autodocs'],
  render: (args) => {
    return html`
      <iai-icon-button
        title=${args.title}
        .handleClick=${args.handleClose}
      >
        ${unsafeHTML(args.icon)}
      </iai-icon-button>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Default = {
  args: {
    title: "Test Title",
    handleClose: action("Close button clicked"),
    icon: `
      <iai-icon
        slot="icon"
        name="close"
        .color=${"var(--iai-colour-text-secondary)"}
      ></iai-icon>
    `,
  },
};
