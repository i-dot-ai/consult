import { afterEach, describe, expect, it } from "vitest";
import { render, cleanup } from "@testing-library/svelte";

import MetricsSummary, { type Props } from "./MetricsSummary.svelte";

describe("MetricsSummary", () => {
  afterEach(() => cleanup());

  it("should render data", () => {
    const TEST_DATA: Props = {
      questionCount: 10,
      responseCount: 20,
      demoCount: 30,
    };

    const { getByText } = render(MetricsSummary, {
      questionCount: TEST_DATA.questionCount,
      responseCount: TEST_DATA.responseCount,
      demoCount: TEST_DATA.demoCount,
    });

    expect(getByText("Responses"));
    expect(getByText(TEST_DATA.responseCount));

    expect(getByText("Questions"));
    expect(getByText(TEST_DATA.questionCount));

    expect(getByText("Demographics"));
    expect(getByText(TEST_DATA.demoCount));
  });
});
