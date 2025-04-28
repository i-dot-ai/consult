import { html } from 'lit';
import { action } from "@storybook/addon-actions";

import IaiRadioInput from './iai-radio-input.lit.csr.mjs';


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Example/IaiRadioInput',
  tags: ['autodocs'],
  argTypes: {
    name: { control: "text" },
  },
  render: (args) => {
    return html`
      ${args.inputs.map(input => html`
        <iai-radio-input
          name=${args.name}  
          .handleChange=${args.handleChange}
          inputId=${input.inputId}
          label=${input.label}
          value=${input.value}
        ></iai-radio-input>  
      `)}
      
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Default = {
  args: {
    name: "radio-selection",
    handleChange: () => action("Selected value changed to:")(event.target.value),
    inputs: [
      {
        value: "selection-value-one",
        label: "Selection Value 1",
        inputId: "selection-value-one"
      },
      {
        value: "selection-value-two",
        label: "Selection Value 2",
        inputId: "selection-value-two"
      },
      {
        value: "selection-value-three",
        label: "Selection Value 3",
        inputId: "selection-value-three"
      },
    ]
  }
};