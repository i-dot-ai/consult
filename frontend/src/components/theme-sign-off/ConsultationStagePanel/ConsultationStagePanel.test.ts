import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/svelte";

import ConsultationStagePanel from "./ConsultationStagePanel.svelte";
import { ConsultationStageNames } from "../../../global/types";

describe("ConsultationStagePanel", () => {
  const id = "test-consultation-id";
  const onConfirmClickMock = vi.fn();

  it("should render correctly for theme_sign_off stage", () => {
    const { container } = render(ConsultationStagePanel, {
      consultation: { id, stage: ConsultationStageNames.THEME_SIGN_OFF },
      questionsCount: 10,
      onConfirmClick: onConfirmClickMock,
    });

    expect(screen.getByText("All Questions Signed Off")).toBeInTheDocument();
    expect(
      screen.getByText(
        /You have successfully reviewed and signed off themes for all 10 consultation questions/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Confirm/i }),
    ).toBeInTheDocument();
    expect(container).toMatchSnapshot();
  });

  it("should render correctly for theme_mapping stage", () => {
    const { container } = render(ConsultationStagePanel, {
      consultation: { id, stage: ConsultationStageNames.THEME_MAPPING },
      questionsCount: 10,
      onConfirmClick: onConfirmClickMock,
    });

    expect(screen.getByText("AI Mapping in Progress")).toBeInTheDocument();
    expect(
      screen.getByText(
        /You have completed the theme sign-off phase for all 10 consultation questions/i,
      ),
    ).toBeInTheDocument();
    expect(container).toMatchSnapshot();
  });

  it("should render correctly for analysis stage", () => {
    const { container } = render(ConsultationStagePanel, {
      consultation: { id, stage: ConsultationStageNames.ANALYSIS },
      questionsCount: 10,
      onConfirmClick: onConfirmClickMock,
    });

    expect(screen.getByText("AI Mapping Complete")).toBeInTheDocument();
    expect(
      screen.getByText(
        /All consultation responses have been successfully mapped/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /Analysis Dashboard/i }),
    ).toBeInTheDocument();
    expect(container).toMatchSnapshot();
  });
});
