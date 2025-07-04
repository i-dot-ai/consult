import { html } from 'lit';
import { action } from "@storybook/addon-actions";

import ToggleInput from './iai-toggle-input.lit.csr.mjs';


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/Inputs/ToggleInput',
  tags: ['autodocs'],
  argTypes: {
    name: { control: "text" },
  },
  render: (args) => {
    return html`
      <iai-toggle-input
        .name=${args.name}  
        .handleChange=${args.handleChange}
        .inputId=${args.inputId}
        .label=${args.label}
        .hideLabel=${args.hideLabel}
        .value=${args.value}
        .checked=${args.checked}
      ></iai-toggle-input>  
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Default = {
  args: {
    name: "toggle-input",
    value: false,
    label: "Toggle Input",
    inputId: "toggle-input",
    checked: false,
    handleChange: (e) => {
      const toggleInputElement = document.querySelector(`iai-toggle-input:has(#toggle-input)`);
      toggleInputElement.value = !(toggleInputElement.value);
      toggleInputElement.checked = toggleInputElement.value;
      action("New value:")(toggleInputElement.value);
    },
  }
};

export const HiddenLabel = {
  args: {
    name: "toggle-input-hiddenlabel",
    value: false,
    label: "Hidden Label Toggle",
    hideLabel: true,
    inputId: "toggle-input-hiddenlabel",
    checked: false,
    handleChange: (e) => {
      const toggleInputElement = document.querySelector(`iai-toggle-input:has(#toggle-input-hiddenlabel)`);
      toggleInputElement.value = !(toggleInputElement.value);
      toggleInputElement.checked = toggleInputElement.value;
      action("New value:")(toggleInputElement.value);
    },
  }
};