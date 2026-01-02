import { describe, expect, it } from "vitest";
import { createRawSnippet } from "svelte";
import { render, screen } from "@testing-library/svelte";

import OrderedList from "./OrderedList.svelte";

describe("OrderedList", () => {
  it("renders list", () => {
    const listItem = `<li>This is a list item</li>`;
    const childComponent = createRawSnippet(() => {
      return {
        render: () => listItem,
      };
    });
    render(OrderedList, { children: childComponent });

    expect(screen.getByText("This is a list item")).toBeTruthy();
  });
});
