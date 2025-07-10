import { html } from 'lit';
import { unsafeHTML } from 'lit/directives/unsafe-html.js';

import IaiDataTable from './iai-data-table.lit.csr.mjs';
import { DEFAULT_DATA } from './testData.mjs';


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/DataTable',
  tags: ['autodocs'],
  argTypes: {
    data: {
      description: "Array of objects with keys as table headers and values as cell content. Cell content can be a string or an html element. If _sortValues key is included with an object whose keys match the table headers, the corresponding values will be used for sorting instead of cell content. If _bottomRow key is added, the row will appear at the bottom regardless of sorting.",
    },
    initialSorts: {
      description: "Used to specify which sorts and directions will be applied on mount. Does not affect how the sort buttons behave after the table is mounted.",
    }
  },
  render: (args) => {
    return html`
      <iai-data-table
        .data=${args.data}
        .initialSorts=${args.initialSorts}
        .sortable=${args.sortable}
      ></iai-data-table>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args

export const DefaultTable = {
  args: {
    data: DEFAULT_DATA,
    initialSorts: [{
      field: "Total mentions",
      ascending: false,
    }],
    sortable: true,
  }
};

export const TableWithRawHtml = {
  args: {
    data: [
      ...DEFAULT_DATA.slice(1),
      {
        ...DEFAULT_DATA[0],
        "Theme name": unsafeHTML(`<span style=\"color: red;\">All Themes</span>`)
      }
    ],
    sortable: true,
  }
};

export const TableWithEncodedProps = {
  args: {
    data: DEFAULT_DATA,
    sortable: true,
  },

  render: (args) => {
    return html`
      <iai-data-table
        .encprops=${btoa(JSON.stringify({"data": args.data}))}
      ></iai-data-table>
    `
  },
};

export const WithInitialSorts = {
  args: {
    data: DEFAULT_DATA,
    initialSorts: [{ "field": "Total mentions", "ascending": false }],
    sortable: true,
  }
};

export const NotSortable = {
  args: {
    data: DEFAULT_DATA,
    sortable: false,
  }
};