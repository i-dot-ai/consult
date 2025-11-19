import { render, fireEvent } from "@testing-library/svelte";
import { describe, it, expect, vi } from "vitest";
import CheckboxGroup from "./CheckboxGroup.svelte";

const mockItems = [
  { value: "question_1", text: "Question 1" },
  { value: "question_2", text: "Question 2" },
  { value: "question_3", text: "Question 3", hint: "This includes all sub-questions" },
  { value: "question_4", text: "Question 4", disabled: true }
];

describe("CheckboxGroup Component", () => {
  it("renders with basic props", () => {
    const { getByRole, getAllByRole } = render(CheckboxGroup, {
      props: {
        name: "question_parts",
        items: mockItems
      }
    });

    const fieldset = getByRole("group");
    const checkboxes = getAllByRole("checkbox");
    
    expect(fieldset).toBeInTheDocument();
    expect(checkboxes).toHaveLength(4);
  });

  it("renders fieldset legend", () => {
    const { getByText } = render(CheckboxGroup, {
      props: {
        name: "question_parts",
        fieldset: {
          legend: {
            text: "Which questions do you want to download data for?",
            classes: "govuk-fieldset__legend--l"
          }
        },
        items: mockItems
      }
    });

    expect(getByText("Which questions do you want to download data for?")).toBeInTheDocument();
  });

  it("renders legend as page heading when isPageHeading is true", () => {
    const { container } = render(CheckboxGroup, {
      props: {
        name: "question_parts",
        fieldset: {
          legend: {
            text: "Main heading",
            isPageHeading: true
          }
        },
        items: mockItems
      }
    });

    const heading = container.querySelector('h1');
    expect(heading).toBeInTheDocument();
    expect(heading).toHaveTextContent("Main heading");
  });

  it("renders all checkbox items", () => {
    const { getByLabelText } = render(CheckboxGroup, {
      props: {
        name: "question_parts",
        items: mockItems
      }
    });

    expect(getByLabelText("Question 1")).toBeInTheDocument();
    expect(getByLabelText("Question 2")).toBeInTheDocument();
    expect(getByLabelText("Question 3")).toBeInTheDocument();
    expect(getByLabelText("Question 4")).toBeInTheDocument();
  });

  it("renders hint text for items that have it", () => {
    const { getByText } = render(CheckboxGroup, {
      props: {
        name: "question_parts",
        items: mockItems
      }
    });

    expect(getByText("This includes all sub-questions")).toBeInTheDocument();
  });

  it("sets correct checked state based on values prop", () => {
    const { getByLabelText } = render(CheckboxGroup, {
      props: {
        name: "question_parts",
        items: mockItems,
        values: ["question_1", "question_3"]
      }
    });

    expect(getByLabelText("Question 1")).toBeChecked();
    expect(getByLabelText("Question 2")).not.toBeChecked();
    expect(getByLabelText("Question 3")).toBeChecked();
  });

  it("calls onchange when checkbox is toggled", async () => {
    const onchange = vi.fn();
    const { getByLabelText } = render(CheckboxGroup, {
      props: {
        name: "question_parts",
        items: mockItems,
        values: [],
        onchange
      }
    });

    await fireEvent.click(getByLabelText("Question 1"));
    expect(onchange).toHaveBeenCalledWith(["question_1"]);
  });

  it("adds and removes values correctly", async () => {
    const onchange = vi.fn();
    const { getByLabelText } = render(CheckboxGroup, {
      props: {
        name: "question_parts",
        items: mockItems,
        values: ["question_1"],
        onchange
      }
    });

    // Add another value
    await fireEvent.click(getByLabelText("Question 2"));
    expect(onchange).toHaveBeenCalledWith(["question_1", "question_2"]);

    // Remove existing value
    await fireEvent.click(getByLabelText("Question 1"));
    expect(onchange).toHaveBeenCalledWith([]);
  });

  it("disables individual checkboxes when item.disabled is true", () => {
    const { getByLabelText } = render(CheckboxGroup, {
      props: {
        name: "question_parts",
        items: mockItems
      }
    });

    expect(getByLabelText("Question 4")).toBeDisabled();
  });

  it("disables all checkboxes when disabled prop is true", () => {
    const { getAllByRole } = render(CheckboxGroup, {
      props: {
        name: "question_parts",
        items: mockItems,
        disabled: true
      }
    });

    const checkboxes = getAllByRole("checkbox");
    checkboxes.forEach(checkbox => {
      expect(checkbox).toBeDisabled();
    });
  });

  it("renders hint text for the group", () => {
    const { getByText } = render(CheckboxGroup, {
      props: {
        name: "question_parts",
        items: mockItems,
        hint: "Select one or more questions"
      }
    });

    expect(getByText("Select one or more questions")).toBeInTheDocument();
  });

  it("renders error message when provided", () => {
    const { getByText } = render(CheckboxGroup, {
      props: {
        name: "question_parts",
        items: mockItems,
        errorMessage: "Please select at least one question"
      }
    });

    expect(getByText("Please select at least one question")).toBeInTheDocument();
  });

  it("applies error styling when error message present", () => {
    const { container } = render(CheckboxGroup, {
      props: {
        name: "question_parts",
        items: mockItems,
        errorMessage: "Error message"
      }
    });

    const formGroup = container.firstChild;
    expect(formGroup).toHaveClass('border-l-4', 'border-red-600');
  });

  it("sets correct aria-describedby attributes", () => {
    const { getAllByRole } = render(CheckboxGroup, {
      props: {
        name: "question_parts",
        items: mockItems,
        hint: "Hint text",
        errorMessage: "Error text"
      }
    });

    const checkboxes = getAllByRole("checkbox");
    checkboxes.forEach(checkbox => {
      expect(checkbox).toHaveAttribute("aria-describedby", "question_parts-hint question_parts-error");
    });
  });

  it("applies correct legend size classes", () => {
    const legendSizes = ['s', 'm', 'l', 'xl'];
    
    legendSizes.forEach(size => {
      const { container } = render(CheckboxGroup, {
        props: {
          name: "test-group",
          fieldset: {
            legend: {
              text: "Test legend",
              classes: `govuk-fieldset__legend--${size}`
            }
          },
          items: mockItems
        }
      });

      const legend = container.querySelector('legend');
      const expectedClasses = {
        's': 'font-semibold',
        'm': 'font-semibold',
        'l': 'font-semibold',
        'xl': 'font-semibold'
      };
      expect(legend).toHaveClass(expectedClasses[size]);
    });
  });

  it("generates correct checkbox IDs and names", () => {
    const { getByLabelText } = render(CheckboxGroup, {
      props: {
        name: "question_parts",
        items: mockItems
      }
    });

    const checkbox1 = getByLabelText("Question 1");
    expect(checkbox1).toHaveAttribute("id", "question_parts-question_1");
    expect(checkbox1).toHaveAttribute("name", "question_parts");
    expect(checkbox1).toHaveAttribute("value", "question_1");
  });
});