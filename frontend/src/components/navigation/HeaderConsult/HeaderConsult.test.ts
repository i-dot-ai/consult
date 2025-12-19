import { describe, expect, it } from "vitest";
import userEvent from "@testing-library/user-event";
import { render, screen, waitFor } from "@testing-library/svelte";

import HeaderConsult, { type Props } from "./HeaderConsult.svelte";

const testData: Props = {
  subtitle: "AI safety and governance framework 2024",
  isSignedIn: true,
  isStaff: true,
  showProcess: true,
  consultationId: "test-id",
  consultationStage: "theme_sign_off",
};

describe("HeaderConsult", () => {
  it("renders title", () => {
    render(HeaderConsult, testData);
    expect(screen.getByText("Consult")).toBeInTheDocument();
  });

  it("renders subtitle", () => {
    render(HeaderConsult, testData);
    expect(screen.getByText(testData.subtitle!)).toBeInTheDocument();
  });

  it("renders path", () => {
    render(HeaderConsult, { ...testData, path: "Dashboard" });
    expect(screen.getByText(`/ Dashboard`)).toBeInTheDocument();
  });

  it("renders manage menu if signed in as staff", () => {
    render(HeaderConsult, testData);
    expect(screen.getByText("Manage")).toBeInTheDocument();
  });

  it("does not render manage menu if signed in but not as staff", () => {
    render(HeaderConsult, { ...testData, isStaff: false });
    expect(screen.queryByText("Manage")).not.toBeInTheDocument();
  });

  it("renders sign out link if signed in", async () => {
    render(HeaderConsult, testData);
    const profileButton = screen.getAllByRole("button").at(4);

    const user = userEvent.setup();
    await user.click(profileButton!);
    await waitFor(() =>
      expect(screen.queryByText("Sign In")).not.toBeInTheDocument(),
    );
    expect(await screen.findByText("Sign Out")).toBeInTheDocument();
  });

  it("does not render sign out link if not signed in", async () => {
    render(HeaderConsult, { ...testData, isSignedIn: false });
    const profileButton = screen.getAllByRole("button").at(4);

    const user = userEvent.setup();
    await user.click(profileButton!);
    expect(await screen.findByText("Sign In")).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.queryByText("Sign Out")).not.toBeInTheDocument(),
    );
  });

  it("renders process button if process is true", async () => {
    render(HeaderConsult, testData);
    expect(screen.getByText("Process")).toBeInTheDocument();
  });

  it("does not render process button if process is not true", async () => {
    render(HeaderConsult, { ...testData, showProcess: false });
    expect(screen.queryByText("Process")).not.toBeInTheDocument();
  });

  it("matches snapshot", async () => {
    const { container } = render(HeaderConsult, testData);
    expect(container).toMatchSnapshot();
  });
});
