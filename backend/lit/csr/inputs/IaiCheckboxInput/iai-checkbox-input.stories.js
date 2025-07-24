import { html } from 'lit';
import { action } from "@storybook/addon-actions";

import IaiCheckboxInput from './iai-checkbox-input.lit.csr.mjs';


let selectedValues = [];

// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/Inputs/CheckboxInput',
  tags: ['autodocs'],
  argTypes: {
    name: { control: "text" },
  },
  render: (args) => {
    return html`
      ${args.inputs.map(input => html`
        <iai-checkbox-input
          name=${args.name}  
          .handleChange=${args.handleChange}
          inputId=${input.inputId}
          label=${input.label}
          value=${input.value}
        ></iai-checkbox-input>
      `)}
      
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Default = {
  args: {
    name: "radio-selection",
    handleChange: () => {
      const clickedValue = event.target.value;
      if (selectedValues.includes(clickedValue)) {
        selectedValues = selectedValues.filter(value => value != clickedValue);
      } else {
        selectedValues.push(clickedValue);
      }
      action("Selected Values:")(selectedValues)
      // action("Checkbox clicked on:")(event.target.value)
    },
    inputs: [
      {
        value: "checkbox-one",
        label: "Checkbox 1",
        inputId: "checkbox-one"
      },
      {
        value: "checkbox-two",
        label: "Checkbox 2",
        inputId: "checkbox-two"
      },
      {
        value: "checkbox-three",
        label: "Checkbox 3",
        inputId: "checkbox-three"
      },
    ]
  }
};