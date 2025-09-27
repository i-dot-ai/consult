import { describe, expect, it } from "vitest";
import { createRawSnippet } from "svelte";
import { render } from "@testing-library/svelte";

import OrderedList from "./OrderedList.svelte";

describe("OrderedList", () => {
  it("renders list", () => {
    const listItem = `<li>This is a list item</li>`;
    const childComponent = createRawSnippet(() => {
      return {
        render: () => listItem,
      };
    });
    const { getByText } = render(OrderedList, { children: childComponent });

    expect(getByText("This is a list item")).toBeTruthy();
  });
});
