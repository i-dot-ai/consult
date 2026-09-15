import { describe, expect, it } from "vitest";
import { createRawSnippet } from "svelte";
import { render, screen } from "@testing-library/svelte";

import Alert, { type Props } from "./Alert.svelte";
import { children, defaultVariant, Icon } from "./testData";

describe("Alert", () => {
    const testData: Props = {
        Icon: Icon,
        children: children,
        variant: defaultVariant,
    };

    it("should render icon", () => {
        render(Alert, testData);
        expect(screen.getByTestId("icon")).toBeInTheDocument();
    });

    it("should render children", () => {
        render(Alert, {
            ...testData,
            children: createRawSnippet(() => ({
                render: () => `<p>Test Content</p>`
            }))
        });
        expect(screen.getByText("Test Content")).toBeInTheDocument();
    });

    it("should match snapshot", () => {
        const { container } = render(Alert, testData);
        expect(container).toMatchSnapshot();
    });

    it.each(["info", "warning", "error", "success"])("should render correct variant", (variant) => {
        render(Alert, {
            ...testData,
            variant: (variant as Props["variant"]),
        });
        expect(screen.getByTestId(`alert-${variant}`)).toBeInTheDocument();
    });
});
