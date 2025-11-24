import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/svelte";

import ConsultationStagePanel from "./ConsultationStagePanel.svelte";

describe("ConsultationStagePanel", () => {
  const baseConsultation = {
    id: "test-consultation-id",
    title: "Test Consultation",
    created_at: "2024-01-01T00:00:00Z",
  };
  const onConfirmClickMock = vi.fn();

  afterEach(() => cleanup());

  describe("Theme Sign Off stage", () => {
    let container: HTMLElement;

    beforeEach(() => {
      const result = render(ConsultationStagePanel, {
        consultation: { ...baseConsultation, stage: "theme_sign_off" },
        questionsCount: 10,
        onConfirmClick: onConfirmClickMock,
      });
      container = result.container;
    });

    it("should render correct title for theme_sign_off stage", () => {
      expect(screen.getByText("All Questions Signed Off"));
    });

    it("should render correct content for theme_sign_off stage", () => {
      expect(
        screen.getByText(
          /You have successfully reviewed and signed off themes for all 10 consultation questions/i,
        ),
      );
    });

    it("should render confirm button for theme_sign_off stage", () => {
      const button = screen.getByRole("button", {
        name: /Confirm and Proceed to Mapping/i,
      });
      expect(button).toBeTruthy();
    });

    it("should match snapshot for theme_sign_off stage", () => {
      expect(container).toMatchSnapshot();
    });
  });

  describe("Theme Mapping stage", () => {
    let container: HTMLElement;

    beforeEach(() => {
      const result = render(ConsultationStagePanel, {
        consultation: { ...baseConsultation, stage: "theme_mapping" },
        questionsCount: 10,
        onConfirmClick: onConfirmClickMock,
      });
      container = result.container;
    });

    it("should render correct title for theme_mapping stage", () => {
      expect(screen.getByText("AI Mapping in Progress"));
    });

    it("should render correct content for theme_mapping stage", () => {
      expect(
        screen.getByText(
          /You have completed the theme sign-off phase for all 10 consultation questions/i,
        ),
      );
    });

    it("should match snapshot for theme_mapping stage", () => {
      expect(container).toMatchSnapshot();
    });
  });

  describe("Analysis stage", () => {
    let container: HTMLElement;

    beforeEach(() => {
      const result = render(ConsultationStagePanel, {
        consultation: { ...baseConsultation, stage: "analysis" },
        questionsCount: 10,
        onConfirmClick: onConfirmClickMock,
      });
      container = result.container;
    });

    it("should render correct title for analysis stage", () => {
      expect(screen.getByText("AI Mapping Complete"));
    });

    it("should render correct content for analysis stage", () => {
      expect(
        screen.getByText(
          /All consultation responses have been successfully mapped/i,
        ),
      );
    });

    it("should render link to Analysis Dashboard", () => {
      const link = screen.getByRole("link", { name: /Analysis Dashboard/i });
      expect(link).toBeTruthy();
    });

    it("should match snapshot for analysis stage", () => {
      expect(container).toMatchSnapshot();
    });
  });
});
