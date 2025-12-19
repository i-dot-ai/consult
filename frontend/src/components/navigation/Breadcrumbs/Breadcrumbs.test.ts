import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import Breadcrumbs from "./Breadcrumbs.svelte";

describe("Breadcrumbs", () => {
  const STAGES = [
    "data_setup",
    "theme_find",
    "theme_sign_off",
    "theme_mapping",
    "quality_check",
    "analysis",
  ];

  it.each(STAGES)("should render the correct stages", async (consultationStage) => {
    render(Breadcrumbs, {
      consultationId: "test-id",
      consultationStage: consultationStage,
    });

    const currentStageIndex = STAGES.findIndex(stage => consultationStage === stage);

    expect(screen.queryAllByTestId("past-stage")).toHaveLength(currentStageIndex);
    expect(screen.queryAllByTestId("future-stage")).toHaveLength(STAGES.length - (currentStageIndex + 1));
    expect(screen.queryAllByTestId("current-stage")).toHaveLength(1);
  });
});
