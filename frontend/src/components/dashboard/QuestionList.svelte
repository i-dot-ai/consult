<script lang="ts">
    import { fade } from "svelte/transition";

    import Link from "../Link.svelte";
    import MaterialIcon from "../MaterialIcon.svelte";
    import Help from "../svg/material/Help.svelte";
    import Star from "../svg/material/Star.svelte";
    import Panel from "./Panel.svelte";
    import Button from "../inputs/Button.svelte";

    import type { Question } from "../../global/types.ts";
    import { getQuestionDetailUrl } from "../../global/enums.ts";
    import { applyHighlight } from "../../global/utils.ts";
    import { favStore } from "../../global/stores.ts";

    export let questions: Consultation;
    export let consultationId: string = "";
    export let highlightText: string = "";
</script>

{#each questions as question}
    <div transition:fade={{duration: 200}} >
        <Link
            variant="block"
            href={getQuestionDetailUrl(consultationId, question.id)}
            title={`Q${question.number}: ${question.question_text}`}
            ariaLabel={`Click to view question: ${question.question_text}`}
        >
            <Panel>
                <article class="flex gap-2 items-start">
                    <div class="mt-0.5">
                        <MaterialIcon size="1.3rem" color="teal">
                            <Help />
                        </MaterialIcon>
                    </div>
                    <div class="grow">
                        <p class="text-md">
                            {@html applyHighlight(`Q${question.number}: ${question.question_text}`, highlightText)}
                        </p>
                        <div class="text-sm mt-2">
                            {question.total_responses} responses
                        </div>
                    </div>
                    <div class="mt-0.5">
                        <Button
                            variant="ghost"
                            handleClick={(e) => {
                                e.stopPropagation();
                                favStore.toggleFav(question.id);
                            }}
                        >
                            <MaterialIcon size="1.3rem" color="gray">
                                <Star fill={$favStore.includes(question.id)} />
                            </MaterialIcon>
                        </Button>
                    </div>
                </article>    
            </Panel>
        </Link>
    </div>
{/each}