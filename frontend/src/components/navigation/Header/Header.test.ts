import { describe, expect, it } from "vitest";
import userEvent from "@testing-library/user-event";
import { render, screen, waitFor } from "@testing-library/svelte";

import Header from "./Header.svelte";

import { testData } from "./testData";

describe("Header", () => {
  it("should render text and navItems", async () => {
    render(Header, {
      ...testData,
    });

    expect(screen.getByText(testData.title)).toBeInTheDocument();
    expect(screen.getByText(testData.subtitle)).toBeInTheDocument();

    expect(screen.getByTestId("consult-icon")).toBeInTheDocument();

    testData.pathParts.forEach((pathPart) => {
      expect(screen.getByText(`/ ${pathPart}`)).toBeInTheDocument();
    });

    testData.navItems.forEach((navItem) => {
      const navEl = screen.getByText(navItem.label);
      expect(navEl).toBeInTheDocument();

      if (navItem.url) {
        // eslint-disable-next-line vitest/no-conditional-expect
        expect(navEl.closest("a")!.getAttribute("href")).toContain(navItem.url);
      }

      if (navItem.children) {
        navItem.children.forEach((subItem) => {
          // eslint-disable-next-line vitest/no-conditional-expect
          expect(screen.getByText(subItem.label)).toBeInTheDocument();
        });
      }
    });
  });

  it("should expand and collapse nav dropdowns", async () => {
    const user = userEvent.setup();

    render(Header, {
      ...testData,
    });

    const dropdownNavItems = testData.navItems.filter((item) =>
      Boolean(item.children),
    );
    const buttons: HTMLElement[] = dropdownNavItems
      .map((item) => item.label)
      .map((label) => screen.getByText(label).closest("button")!);

    expect(buttons).toHaveLength(
      testData.navItems.filter((item) => Boolean(item.children)).length,
    );

    buttons.forEach(async (button) => {
      expect(button.getAttribute("aria-expanded")).toEqual("false");

      await user.click(button);

      await waitFor(() => {
        expect(button.getAttribute("aria-expanded")).toEqual("true");
      });
    });
  });

  it("should not render mobile nav if mobile button has not been clicked", async () => {
    const user = userEvent.setup();

    render(Header, {
      ...testData,
    });

    expect(screen.queryByTestId("mobile-nav")).toBeFalsy();

    const button = screen.getByTestId("mobile-menu-button");
    await user.click(button);

    expect(await screen.findByTestId("mobile-nav")).toBeInTheDocument();
  });
});
