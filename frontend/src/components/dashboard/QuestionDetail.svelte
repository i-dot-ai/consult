<script lang="ts">
    import clsx from "clsx";

    import { onMount } from "svelte";
    import { slide } from "svelte/transition";

    import MaterialIcon from "../MaterialIcon.svelte";
    import Button from "../inputs/Button.svelte";
    import Panel from "../dashboard/Panel.svelte";
    import Star from "../svg/material/Star.svelte";
    import SearchCard from "./SearchCard.svelte";
    import QuestionCard from "./QuestionCard.svelte";

    import { getConsultationDetailUrl } from "../../global/routes.ts";
    import { createFetchStore } from "../../global/stores.ts";

    export let consultationId: string = "";
    export let questionId: string = "";

    let consultation: Consultation;
    let answers;

    const {
        loading: isConsultationLoading,
        error: consultationError,
        load: loadConsultation,
        data: consultationData,
    } = createFetchStore(`/api/consultations/${consultationId}/`);

    const {
        loading: isAnswersLoading,
        error: answersError,
        load: loadAnswers,
        data: answersData,
    } = createFetchStore(`/api/consultations/${consultationId}/questions/${questionId}/filtered-responses/`);

    onMount(async () => {
        loadConsultation();
        loadAnswers();
    })
</script>

<section class={clsx([
    "flex",
    "justify-between",
    "flex-wrap",
    "gap-2",
    "items-center",
])}>
    <Button handleClick={() => {
        window.location.href = getConsultationDetailUrl(consultationId);
    }}>
        <MaterialIcon class="shrink-0">
            <Star />
        </MaterialIcon>
        <span class="text-sm">Back to all questions</span>
    </Button>

    <small>
        Choose a different question to analyse
    </small>
</section>

<section>
    {#if $isConsultationLoading}
        <p transition:slide>Loading consultation</p>
    {:else if $consultationError}
        <p transition:slide>Consultation Error: {$consultationError}</p>
    {:else}
        <QuestionCard
            clickable={true}
            consultationId={$consultationData.id}
            question={$consultationData.questions?.find(question => question.id === questionId)}
        />
    {/if}
</section>

<section>
    {#if $isAnswersLoading}
        <p>Loading answers...</p>
    {:else if $answersError}
        <p>Answers Error: {$answersError}</p>
    {:else}
        <p>Answers loaded</p>
    {/if}
</section>