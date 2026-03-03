import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import IntroCard from "./IntroCard.svelte";
import { TEST_DATA } from "./testData";

// Icon: UnknownDocument,
//   order: 1,
//   title: "Prepare data outside Consult",
//   subtitle: "Export from your collection tool and structure your files",
//   isActive: true,
//   showArrow: true,

describe("IntroCard", () => {
  const testData = TEST_DATA;

  it("should render order number text", () => {
    render(IntroCard, testData);

    expect(
      screen.getByText(`Step ${testData.order}`),
    ).toBeInTheDocument();
  });

  it("should render title", () => {
    render(IntroCard, testData);

    expect(
      screen.getByText(testData.title),
    ).toBeInTheDocument();
  });

  it("should render subtitle", () => {
    render(IntroCard, testData);

    expect(
      screen.getByText(testData.subtitle),
    ).toBeInTheDocument();
  });

  it("should render arrow", () => {
    render(IntroCard, testData);

    expect(
      screen.getByTestId("intro-card-arrow"),
    ).toBeInTheDocument();
  });

  it("should not render arrow if showArrow is false", () => {
    render(IntroCard, { ...testData, showArrow: false });

    expect(
      screen.queryByTestId("intro-card-arrow"),
    ).not.toBeInTheDocument();
  });

  it("should render as current if isActive is true", () => {
    render(IntroCard, testData);

    expect(
      screen.getByTestId("intro-card"),
    ).toHaveAttribute("aria-current", "true");
  });

  it("should not render as current if isActive is false", () => {
    render(IntroCard, { ...testData, isActive: false });

    expect(
      screen.queryByTestId("intro-card"),
    ).not.toHaveAttribute("aria-current");
  });

  it("should match snapshot", () => {
    const { container } = render(IntroCard, testData);
    expect(container).toMatchSnapshot();
  });
});
