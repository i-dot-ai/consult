<script lang="ts">
    import clsx from "clsx";

    import { fade } from "svelte/transition";

    import type { Question } from "../../global/types.ts";
    import { favStore } from "../../global/stores.ts";
    import { getQuestionDetailUrl } from "../../global/routes.ts";
    import { applyHighlight } from "../../global/utils.ts";

    import MaterialIcon from "../MaterialIcon.svelte";
    import ConditionalRender from "../ConditionalRender.svelte";
    import Star from "../svg/material/Star.svelte";
    import Help from "../svg/material/Help.svelte";
    import Panel from "./Panel.svelte";
    import Link from "../Link.svelte";
    import Button from "../inputs/Button.svelte";

    export let consultationId: string = "";
    export let question: Question = {};
    export let highlightText: string = "";
    export let clickable: boolean = false;
    export let skeleton: boolean = false;

    let skeletonBlink: boolean = false;
    let skeletonIntervalId;

    $: {
        clearInterval(skeletonIntervalId);

        if (skeleton) {
            skeletonIntervalId = setInterval(() => skeletonBlink = !skeletonBlink, 1000);
        }
    }
</script>

<div transition:fade={{duration: 200}} >
    <ConditionalRender
        element={Link}
        condition={clickable && !skeleton}
        variant="block"
        href={getQuestionDetailUrl(consultationId, question.id)}
        title={`Q${question.number}: ${question.question_text}`}
        ariaLabel={`Click to view question: ${question.question_text}`}
    >
        <Panel>
            <article class="flex gap-2 items-start">
                <div class="mt-0.5">
                    {#if !skeleton}
                        <MaterialIcon size="1.3rem" color="fill-teal-500">
                            <Help />
                        </MaterialIcon>
                    {/if}
                </div>
                <div class="grow">
                    {#if skeleton}
                        <p class={clsx([
                            "text-md",
                            "transition-colors",
                            "duration-1000",
                            "select-none",
                            skeletonBlink
                                ? " bg-neutral-200 text-neutral-200"
                                : " bg-neutral-100 text-neutral-100"
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
                                skeletonBlink
                                    ? "bg-neutral-200 text-neutral-200"
                                    : "bg-neutral-100 text-neutral-100"
                            ])
                        ])}>
                            000 responses
                        </div>
                    {:else}
                        <p in:fade class="text-md">
                            {@html applyHighlight(`Q${question.number}: ${question.question_text}`, highlightText)}
                        </p>

                        <div in:fade class="text-sm mt-2">
                            {question.total_responses} responses
                        </div>
                    {/if}
                </div>
                <div class="mt-0.5">
                    {#if !skeleton}
                        <Button
                            variant="ghost"
                            handleClick={(e) => {
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
                    {/if}
                </div>
            </article>    
        </Panel>
    </ConditionalRender>
</div>