import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/svelte";
import userEvent from "@testing-library/user-event";

import ErrorSavingTheme, {
  type SaveThemeError,
} from "./ErrorSavingTheme.svelte";

type ErrorSavingThemeProps = SaveThemeError & { onClose: () => void };

describe("ErrorSavingTheme", () => {
  const testData: ErrorSavingThemeProps = {
    type: "unexpected",
    onClose: vi.fn(),
  };

  it("should render message initially", async () => {
    render(ErrorSavingTheme, testData);

    expect(screen.getByTestId("content")).toBeInTheDocument();
  });

  it.each(["edit-conflict", "remove-conflict"])(
    "should render modified date and person",
    (type) => {
      const LAST_MODIFIED_BY = "test-person";
      const LATEST_VERSION = "12345";
      render(ErrorSavingTheme, {
        type: type as ErrorSavingThemeProps["type"],
        lastModifiedBy: LAST_MODIFIED_BY,
        latestVersion: LATEST_VERSION,
        onClose: testData.onClose,
      });

      expect(screen.getByTestId("content")).toHaveTextContent(LAST_MODIFIED_BY);
    },
  );

  it("should close when close button is clicked", async () => {
    const user = userEvent.setup();
    const onCloseMock = vi.fn();
    render(ErrorSavingTheme, {
      ...testData,
      onClose: onCloseMock,
    });

    const button = screen.getByRole("button");
    await user.click(button);

    expect(screen.queryByTestId("content")).not.toBeInTheDocument();
    expect(onCloseMock).toHaveBeenCalledOnce();
  });

  it("should render correct message for unexpected error", async () => {
    render(ErrorSavingTheme, testData);

    expect(screen.getByTestId("content")).toHaveTextContent(
      "An unexpected error occurred and your changes have not been saved",
    );
  });
});
