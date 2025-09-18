import { afterEach, beforeEach, describe, expect, it, test, vi } from "vitest";
import userEvent from '@testing-library/user-event';
import { render, cleanup, screen } from "@testing-library/svelte";

import Metrics from "./Metrics.svelte";


let testData;

describe("Metrics", () => {
    beforeEach(() => {
        testData = {
            loading: false,
            questions: [
                {
                    id: "test-question-1-id",
                    number: 1,
                    total_responses: 10,
                    question_text: "Test question 1 text",
                    slug: "test-question-1-slug",
                    has_free_text: false,
                    has_multiple_choice: true,
                    multiple_choice_answer: [
                        {
                            id: "multi-answer-1",
                            text: "Multi Answer 1",
                            response_count: 10,
                        },
                        {
                            id: "multi-answer-2",
                            text: "Multi Answer 2",
                            response_count: 20,
                        },
                    ],
                    proportion_of_audited_answers: 0,
                },
            ],
            demoOptions: [
                {
                    name: "Demo Option Category 1",
                    value: "Category 1 Demo Option 1",
                    count: 100,
                },
                {
                    name: "Demo Option Category 1",
                    value: "Category 1 Demo Option 2",
                    count: 200,
                },
                {
                    name: "Demo Option Category 2",
                    value: "Category 2 Demo Option 1",
                    count: 300,
                },
                {
                    name: "Demo Option Category 2",
                    value: "Category 2 Demo Option 2",
                    count: 400,
                },
            ],
            demoOptionsLoading: false,
        };
    })
    afterEach(() => {
        cleanup();
    })

    it("should not render chart if no question has multi answers", () => {
        const { getByText, getAllByText, getByTestId, queryByTestId } = render(Metrics, {
            loading: false,
            questions: testData.questions.map(question => ({
                ...question,
                has_multiple_choice: false,
                multiple_choice_answer: [],
            })),
            demoOptions: testData.demoOptions,
            demoOptionsLoading: false,
        });
        expect(queryByTestId("metrics-chart")).toBeNull();
    })

    it("should render chart if some questions have multi answers", () => {
        const { getByText, getAllByText, getByTestId, queryByTestId } = render(Metrics, {
            loading: false,
            questions: testData.questions,
            demoOptions: testData.demoOptions,
            demoOptionsLoading: false,
        });
        expect(getByTestId("metrics-chart"));
    })

    it("should render demo options data", () => {
        const { getByText } = render(Metrics, {
            loading: false,
            questions: testData.questions,
            demoOptions: testData.demoOptions,
            demoOptionsLoading: false,
        });

        expect(getByText("Demographics Breakdown"));

        testData.demoOptions.forEach((opt) => {
            expect(getByText(opt.name));
            expect(getByText(opt.value));
            expect(getByText(opt.count));
        });
    })

    it("should not render demo options section if no data", () => {
        const { queryByText } = render(Metrics, {
            loading: false,
            questions: testData.questions,
            demoOptions: [],
            demoOptionsLoading: false,
        });
        expect(queryByText("Demographics Breakdown")).toBeNull();
    })
})