export const DATA = [200, 400];
export const LONG_DATA = Array.from(Array(10).keys());

export const LABELS = [
  { count: 200, text: "first item" },
  { count: 400, text: "second item" },
];
export const LONG_LABELS = LONG_DATA.map((count) => ({
  text: `Item ${count}`,
  count,
}));

export const LEGEND_ID = "test-legend";
export const INTERACTIVE = true;
