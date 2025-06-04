import { html } from 'lit';

import IaiCsvDownload from './iai-csv-download.lit.csr.mjs';
import { DEFAULT_DATA } from './testData.mjs';


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/CsvDownload',
  tags: ['autodocs'],
  render: (args) => {
    return html`
      <iai-csv-download
        .fileName=${args.fileName}
        .data=${args.data}
      ></iai-csv-download>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const WithEncProps = {
  args: {
    data: DEFAULT_DATA,
    fileName: "example_data.csv",
  },
  render: (args) => {
    return html`
      <iai-csv-download
        .encprops=${btoa(JSON.stringify({data: args.data}))}
        .fileName=${args.fileName}
      ></iai-csv-download>
    `
  },
};

export const WithProps = {
  args: {
    data: DEFAULT_DATA,
    fileName: "example_data.csv",
  }
};