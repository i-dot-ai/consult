import Pagination from "./Pagination.svelte";

const noop = () => {};

export default {
  name: "Pagination",
  component: Pagination,
  category: "Navigation",
  props: [
    { name: "totalItems", value: 14, type: "number" },
    { name: "currentPage", value: 1, type: "number" },
    { name: "pageSize", value: 10, type: "number" },
  ],
  stories: [
    {
      name: "Two pages",
      props: {
        id: "two-pages",
        totalItems: 14,
        currentPage: 1,
        pageSize: 10,
        onPageChange: noop,
        onPageSizeChange: noop,
      },
    },
    {
      name: "Many pages, in the middle",
      props: {
        id: "many-pages",
        totalItems: 96,
        currentPage: 5,
        pageSize: 10,
        onPageChange: noop,
        onPageSizeChange: noop,
      },
    },
  ],
};
