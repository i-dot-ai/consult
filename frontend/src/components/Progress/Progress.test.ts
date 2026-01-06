import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import Progress from "./Progress.svelte";
import ProgressStory from "./ProgressStory.svelte";

interface Props {
  thickness: 1 | 1.5 | 2;
  value: number;
  transitionDelay: number;
  transitionDuration: number;
}

describe("Progress", () => {
  it.each([10, -10, 50, 0, 100, 1000])(
    "should render correct value",
    (value) => {
      render(Progress, { value: value });

      const expectedValue = value.toString();
      expect(screen.getByRole("meter")).toHaveAttribute(
        "data-value",
        expectedValue,
      );
      expect(screen.getByRole("meter")).toHaveAttribute(
        "aria-valuenow",
        expectedValue,
      );
    },
  );

  it("should have max value of 100", () => {
    render(Progress, { value: 1000 });

    const expectedValue = "100";
    expect(screen.getByRole("meter")).toHaveAttribute(
      "data-max",
      expectedValue,
    );
    expect(screen.getByRole("meter")).toHaveAttribute("max", expectedValue);
    expect(screen.getByRole("meter")).toHaveAttribute(
      "aria-valuemax",
      expectedValue,
    );
  });

  it("should have min value of 0", () => {
    render(Progress, { value: -100 });

    expect(screen.getByRole("meter")).toHaveAttribute("aria-valuemin", "0");
  });

  it.each([1, 1.5, 2])("should render correct thickness", (thickness) => {
    const { container } = render(Progress, {
      value: 50,
      thickness: thickness as Props["thickness"],
    });

    expect(container).toMatchSnapshot();
  });

  it.each([1, 2, 20, 20.5, -10, 0])(
    "should render correct transition delay",
    (transitionDelay) => {
      const { container } = render(Progress, {
        value: 50,
        transitionDelay: transitionDelay,
      });

      expect(container).toMatchSnapshot();
    },
  );

  it.each([1, 2, 20, 20.5, -10, 0])(
    "should render correct transition duration",
    (transitionDuration) => {
      const { container } = render(Progress, {
        value: 50,
        transitionDuration: transitionDuration,
      });

      expect(container).toMatchSnapshot();
    },
  );

  it("should have a story configured correctly", () => {
    expect(ProgressStory).toHaveProperty("name", "Progress");
    expect(ProgressStory).toHaveProperty("component", Progress);
    expect(ProgressStory).toHaveProperty("props");

    const propsDefined = ProgressStory.props.map((prop) => prop.name);
    expect(propsDefined).toEqual([
      "value",
      "thickness",
      "transitionDelay",
      "transitionDuration",
    ]);
  });
});
