<script lang="ts">
    import type { Question } from "../../global/types.ts";
    import { favStore } from "../../global/stores.ts";
    import { getQuestionDetailUrl } from "../../global/routes.ts";
    import { applyHighlight } from "../../global/utils.ts";

    import MaterialIcon from "../MaterialIcon.svelte";
    import Star from "../svg/material/Star.svelte";
    import Help from "../svg/material/Help.svelte";
    import Panel from "./Panel.svelte";
    import Link from "../Link.svelte";
    import Button from "../inputs/Button.svelte";

    export let consultationId: string = "";
    export let question: Question = {};
    export let highlightText: string = "";
    export let clickable: boolean = false;
</script>

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