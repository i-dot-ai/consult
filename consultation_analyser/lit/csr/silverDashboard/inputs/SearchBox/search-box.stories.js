import { html } from 'lit';

import { action } from "@storybook/addon-actions";

import SearchBox from './search-box.lit.csr.mjs';


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/SilverDashboard/SearchBox',
  tags: ['autodocs'],
  render: (args) => {
    return html`
      <iai-silver-search-box
        .inputId=${args.inputId}
        .name=${args.name}
        .label=${args.label}
        .placeholder=${args.placeholder}
        .value=${args.value}
        .hideLabel=${args.hideLabel}
        .handleInput=${args.handleInput}
      ></iai-silver-search-box>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Default = {
  args: {
    inputId: "default-search",
    name: "default-search",
    label: "Search",
    placeholder: "Search consultations...",
    value: "",
    hideLabel: true,
    handleInput: () => action("Input event fired")(event.target.value),
  },
};

export const WithLabel = {
  args: {
    inputId: "default-search",
    name: "default-search",
    label: "Search",
    placeholder: "Search consultations...",
    value: "",
    hideLabel: false,
    handleInput: () => action("Input event fired: ")(event.target.value),
  },
};
