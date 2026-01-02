import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import Accordion, { type Props } from "./Accordion.svelte";
import { createRawSnippet } from "svelte";
import userEvent from "@testing-library/user-event";
import AccordionStory from "./AccordionStory.svelte";

describe("Accordion", () => {
  const testData = {
    content: createRawSnippet(() => ({
      render: () => "<p>Test Contents</p>",
    })),
    title: createRawSnippet(() => ({
      render: () => "<h2>Test Title</h2>",
    }))
  }

  it("should render title", () => {
    render(Accordion, testData);
    expect(screen.getByText("Test Title")).toBeInTheDocument();
  });
  it("should not render contents initially", () => {
    render(Accordion, testData);
    expect(screen.queryByText("Test Contents")).not.toBeInTheDocument();
  });
  it.each(["light", "gray"])("should render correctly", (variant) => {
    const { container } = render(Accordion, {
      ...testData,
      variant: variant as Props["variant"],
    });
    expect(container).toMatchSnapshot();
  });
  it("should render contents when expanded", async () => {
    const user = userEvent.setup();
    render(Accordion, testData);

    const button = screen.getByRole("button");
    await user.click(button);

    expect(screen.queryByText("Test Contents")).toBeInTheDocument();
  });

  it("should have a story configured correctly", () => {
    expect(AccordionStory).toHaveProperty("name", "Accordion");
    expect(AccordionStory).toHaveProperty("component", Accordion);
    expect(AccordionStory).toHaveProperty("props");

    const propsDefined = AccordionStory.props.map(prop => prop.name);
    expect(propsDefined).toEqual(["title", "content"]);
  })
});
