<script lang="ts">
    import clsx from "clsx";

    import { fade } from "svelte/transition";

    import type { Question } from "../../../global/types.ts";
    import { favStore } from "../../../global/stores.ts";
    import { getQuestionDetailUrl } from "../../../global/routes.ts";
    import { applyHighlight } from "../../../global/utils.ts";

    import MaterialIcon from "../../MaterialIcon.svelte";
    import ConditionalWrapper from "../../ConditionalWrapper/ConditionalWrapper.svelte";
    import Star from "../../svg/material/Star.svelte";
    import Help from "../../svg/material/Help.svelte";
    import Panel from "../Panel.svelte";
    import Link from "../../Link.svelte";
    import Button from "../../inputs/Button/Button.svelte";

    export let consultationId: string = "";
    export let question: Question = {};
    export let highlightText: string = "";
    export let clickable: boolean = false;
    export let skeleton: boolean = false;
    export let hideIcon: boolean = false;
    export let horizontal: boolean = false;
</script>

<div class="bg-white" transition:fade={{duration: 200}} >
    <ConditionalWrapper
        element={Link}
        condition={clickable && !skeleton}
        variant="block"
        href={getQuestionDetailUrl(consultationId, question.id)}
        title={`Q${question.number}: ${question.question_text}`}
        ariaLabel={`Click to view question: ${question.question_text}`}
    >
        <Panel>
            <article class={clsx([
                "flex",
                "gap-2",
                "items-start",
                "relative",
                "flex-col-reverse",
                "sm:flex-row",
            ])}>
                <div class={clsx([
                    "mt-0.5",
                    "hidden",
                    "sm:block",
                ])}>
                    {#if !skeleton && !hideIcon}
                        <div data-testid="question-icon">
                            <MaterialIcon size="1.3rem" color="fill-teal-500">
                                <Help />
                            </MaterialIcon>
                        </div>
                    {/if}
                </div>
                <div
                    data-testid="horizontal-container"
                    class={clsx([
                        "grow",
                        horizontal && (clsx([
                            "sm:flex",
                            "justify-between",
                            "items-start",
                            "gap-4",
                        ])),
                ])}>
                    {#if skeleton}
                        <p class={clsx([
                            "text-md",
                            "transition-colors",
                            "duration-1000",
                            "select-none",
                            "bg-neutral-100",
                            "text-neutral-100",
                            "blink",
                        ])}>
                            {"SKELETON ".repeat(20)}
                        </p>

                        <div class={clsx([
                            "text-sm",
                            "mt-2",
                            "transition-colors",
                            "duration-1000",
                            skeleton && clsx([
                                "w-max",
                                "select-none",
                                "bg-neutral-100",
                                "text-neutral-100",
                                "blink",
                            ])
                        ])}>
                            000 responses
                        </div>
                    {:else}
                        <p in:fade class="text-md leading-6">
                            {@html applyHighlight(`Q${question.number}: ${question.question_text}`, highlightText)}
                        </p>

                        <div in:fade class={clsx([
                            "text-sm",
                            "leading-6",
                            "whitespace-nowrap",
                        ])}>
                            {question.total_responses} responses
                        </div>
                    {/if}
                </div>
                <div class={clsx([
                    "-ml-2",
                    "sm:ml-0",
                    horizontal ? "-mt-0.5" : "-mt-1",
                ])}>
                    {#if !skeleton}
                        <div data-testid="fav-button">
                            <Button
                                variant="ghost"
                                handleClick={(e: MouseEvent) => {
                                    e.stopPropagation();
                                    favStore.toggleFav(question.id);
                                }}
                            >
                                {@const favourited = $favStore.includes(question.id)}
                                <MaterialIcon
                                    size="1.3rem"
                                    color={favourited ? "fill-yellow-500" : "fill-gray-500"
                                }>
                                    <Star fill={favourited} />
                                </MaterialIcon>
                            </Button>
                        </div>
                    {/if}
                </div>
            </article>    
        </Panel>
    </ConditionalWrapper>
</div>