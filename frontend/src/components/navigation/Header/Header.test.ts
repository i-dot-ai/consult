import { describe, expect, it } from "vitest";
import userEvent from "@testing-library/user-event";
import { render, screen, waitFor } from "@testing-library/svelte";

import Header from "./Header.svelte";

import { testData } from "./testData";
import type { NavItem, Props } from "./types";

function getNavItemsWithUrl(data: Props) {
  return data.navItems.filter((item) => Boolean(item.url));
}
function getDropdownNavItems(data: Props) {
  return data.navItems.filter((item) => Boolean(item.children));
}

describe("Header", () => {
  it("renders title", () => {
    render(Header, testData);
    expect(screen.getByText(testData.title)).toBeInTheDocument();
  });

  it("renders subtitle", () => {
    render(Header, testData);
    expect(screen.getByText(testData.subtitle)).toBeInTheDocument();
  });

  it.each(testData.pathParts)("renders path part", async (pathPart: string) => {
    render(Header, testData);
    expect(screen.getByText(`/ ${pathPart}`)).toBeInTheDocument();
  });

  it.each(getNavItemsWithUrl(testData))(
    "renders nav items with url",
    async (navItem: NavItem) => {
      render(Header, testData);
      const link = screen.getByRole("link", { name: navItem.label });
      expect(link).toHaveAttribute("href", navItem.url);
    },
  );

  it.each(getDropdownNavItems(testData))(
    "renders dropdown nav items",
    async (navItem: NavItem) => {
      render(Header, testData);
      const dropdownItem = screen.getByRole("button", { name: navItem.label });
      expect(dropdownItem).toBeInTheDocument();
    },
  );

  it("should expand and collapse nav dropdowns", async () => {
    render(Header, testData);

    const user = userEvent.setup();

    const dropdownNavItems = getDropdownNavItems(testData);

    const buttons: HTMLElement[] = dropdownNavItems
      .map((item) => item.label)
      .map((label) => screen.getByRole("button", { name: label }));

    expect(buttons).toHaveLength(dropdownNavItems.length);

    buttons.forEach(async (button) => {
      expect(button).toHaveAttribute("aria-expanded", "false");

      await user.click(button);

      await waitFor(() => {
        expect(button).toHaveAttribute("aria-expanded", "true");
      });
    });
  });

  it("should not render mobile nav if mobile button has not been clicked", async () => {
    render(Header, testData);

    const user = userEvent.setup();

    expect(screen.queryByTestId("mobile-nav")).toBeFalsy();

    const button = screen.getByTestId("mobile-menu-button");
    await user.click(button);

    expect(await screen.findByTestId("mobile-nav")).toBeInTheDocument();
  });
});
