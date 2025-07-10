import { html } from 'lit';

import { action } from "@storybook/addon-actions";

import Tag from './tag.lit.csr.mjs';
import IaiIconButton from '../../questionsArchive/IaiIconButton/iai-icon-button.lit.csr.mjs';
import IaiIcon from '../../IaiIcon/iai-icon.mjs';


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/SilverDashboard/Tag',
  tags: ['autodocs'],
  render: (args) => {
    return html`
      <iai-silver-tag
        .status=${args.status}
        .text=${args.text}
        .subtext=${args.subtext}
        .icon=${args.icon}
        .matchBackground=${args.matchBackground}
      ></iai-silver-tag>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Default = {
  args: {
    text: "Default Tag",
    subtext: "This is the default tag",
    icon: "help",
  },
};

export const DefaultTextOnly = {
  args: {
    text: "Default Tag",
  },
};

export const DefaultMatchBackground = {
  args: {
    text: "Default Tag",
    matchBackground: true,
  },
};

export const Open = {
  args: {
    status: "Open",
    text: "Open",
    icon: "star",
  },
};

export const Closed = {
  args: {
    status: "Closed",
    text: "Closed",
    icon: "help",
  },
};

export const WithSubtext = {
  args: {
    status: "Closed",
    text: "Closed",
    subtext: "This is closed",
    icon: "help",
  },
};

export const LongTextWithButton = {
  render: (args) => {
    return html`
      <style>
        iai-icon-button button {
          font-size: 0.8em;
        }
        iai-silver-tag .text-section {
          display: flex;
          gap: 0.5em;
        }
      </style>
      <iai-silver-tag
        .status=${"Open"}
        .text=${html`
          <div class="text-section">
            <span>
              Tip: Use the filters below to refine responses by demographics, themes, or search for specific keywords. You can select up to 3 themes simultaneously.
            </span>
            <iai-icon-button .handleClick=${() => action("Close button clicked")()}>
              <iai-icon
                slot="icon"
                .name=${"close"}
              ></iai-icon>
            </iai-icon-button>
          </div>
        `}
        .icon=${"help"}
      ></iai-silver-tag>
    `
  },
}