<script lang="ts">
    import { fade } from "svelte/transition";

    import Link from "../Link.svelte";
    import MaterialIcon from "../MaterialIcon.svelte";
    import Help from "../svg/material/Help.svelte";
    import Star from "../svg/material/Star.svelte";
    import Panel from "./Panel.svelte";
    import QuestionCard from "./QuestionCard.svelte";
    import Button from "../inputs/Button.svelte";

    import type { Question } from "../../global/types.ts";
    import { getQuestionDetailUrl } from "../../global/routes.ts";
    import { applyHighlight } from "../../global/utils.ts";
    import { favStore } from "../../global/stores.ts";

    export let questions: Consultation;
    export let consultationId: string = "";
    export let highlightText: string = "";
</script>

{#each questions as question}
    <QuestionCard
        consultationId={consultationId}
        question={question}
        highlightText={highlightText}
        clickable={true}
    />
{/each}