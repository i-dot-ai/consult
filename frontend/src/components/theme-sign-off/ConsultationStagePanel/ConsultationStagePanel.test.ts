import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/svelte";

import ConsultationStagePanel from "./ConsultationStagePanel.svelte";

describe("ConsultationStagePanel", () => {
  const id = "test-consultation-id";
  const onConfirmClickMock = vi.fn();

  it("should show progress when finalising and not all questions signed off", () => {
    render(ConsultationStagePanel, {
      consultation: { id, stage: "theme_sign_off" },
      questionsCount: 10,
      finalisedQuestionCount: 3,
      allQuestionsFinalised: false,
      onConfirmClick: onConfirmClickMock,
    });

    expect(screen.getByText("Finalising Themes")).toBeInTheDocument();
    expect(
      screen.getByText(/3 of 10 questions signed off/i),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Confirm/i }),
    ).not.toBeInTheDocument();
  });

  it("should show confirm button when finalising and all questions signed off", () => {
    render(ConsultationStagePanel, {
      consultation: { id, stage: "theme_sign_off" },
      questionsCount: 10,
      finalisedQuestionCount: 10,
      allQuestionsFinalised: true,
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
  });

  it("should render correctly for theme_mapping stage", () => {
    render(ConsultationStagePanel, {
      consultation: { id, stage: "theme_mapping" },
      questionsCount: 10,
      finalisedQuestionCount: 10,
      allQuestionsFinalised: true,
      onConfirmClick: onConfirmClickMock,
    });

    expect(screen.getByText("AI Mapping in Progress")).toBeInTheDocument();
    expect(
      screen.getByText(
        /You have completed the theme sign-off phase for all 10 consultation questions/i,
      ),
    ).toBeInTheDocument();
  });

  it("should render correctly for analysis stage", () => {
    render(ConsultationStagePanel, {
      consultation: { id, stage: "analysis" },
      questionsCount: 10,
      finalisedQuestionCount: 10,
      allQuestionsFinalised: true,
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
  });
});
