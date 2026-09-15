import { describe, expect, it } from "vitest";
import { createRawSnippet } from "svelte";
import { render, screen } from "@testing-library/svelte";

import Alert from "./Alert.svelte";
import { children, Icon } from "./testData";

describe("Alert", () => {
    const testData = {
        Icon: Icon,
        children: children,
    }

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

    it("should match snapshot initially", () => {
        const { container } = render(Alert, testData);
        expect(container).toMatchSnapshot();
    });
});
