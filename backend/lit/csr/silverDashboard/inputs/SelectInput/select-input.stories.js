import { html } from 'lit';
import { action } from "@storybook/addon-actions";

import SelectInput from './select-input.lit.csr.mjs';


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/SilverDashboard/SelectInput',
  tags: ['autodocs'],
  argTypes: {
    inputId: { control: "text" },
    name: { control: "text" },
    label: { control: "text" },
    placeholder: { control: "text" },
    value: { control: "text" },
  },
  render: (args) => {
    return html`
      <iai-silver-select-input
        inputId=${args.inputId}  
        name=${args.name}
        label=${args.label}
        placeholder=${args.placeholder}
        .value=${args.value}
        .options=${args.options}
        .handleChange=${args.handleChange}
        .horizontal=${args.horizontal}
      ></iai-silver-select-input>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Default = {
  args: {
    inputId: "select-input-example",
    name: "select-input-example",
    label: "Select Input Example",
    placeholder: "Select an option...",
    value: "",
    options: [
      { value: "selection-one", text: "Selection 1" },
      { value: "selection-two", text: "Selection 2" },
      { value: "selection-three", text: "Selection 3" },
    ],
    handleChange: () => action("Selected value changed to:")(event.target.value),
  }
};

export const ValuePreselected = {
  args: {
    inputId: "select-input-example",
    name: "select-input-example",
    label: "Select Input Example",
    placeholder: "Select an option...",
    value: "selection-three",
    options: [
      { value: "selection-one", text: "Selection 1" },
      { value: "selection-two", text: "Selection 2" },
      { value: "selection-three", text: "Selection 3" },
    ],
    handleChange: () => action("Selected value changed to:")(event.target.value),
  }
};

export const Horizontal = {
  args: {
    inputId: "select-input-example",
    name: "select-input-example",
    label: "Select Input Example",
    placeholder: "Select an option...",
    value: "selection-three",
    options: [
      { value: "selection-one", text: "Selection 1" },
      { value: "selection-two", text: "Selection 2" },
      { value: "selection-three", text: "Selection 3" },
    ],
    handleChange: () => action("Selected value changed to:")(event.target.value),
    horizontal: true,
  }
};