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

    export let consultationId: string = "";
    export let questionId: string = "";

    let consultation: Consultation;
    let answers;
    let loading: boolean = true;
    let error: string = "";

    onMount(async () => {
        try {
            const consultationResponse = await fetch(`/api/consultations/${consultationId}/`);
            if (!consultationResponse.ok) {
                error = "consultationResponse not ok";
                return;
            }
            consultation = await consultationResponse.json();
            error = "";
        } catch(err) {
            error = err.message;
        } finally {
            loading = false;
        }
    })
    onMount(async () => {
        try {
            const filteredAnswers = await fetch(`/api/consultations/${consultationId}/questions/${questionId}/filtered-responses/`);
            if (!filteredAnswers.ok) {
                error = "filteredAnswers not ok";
                return;
            }
            answers = await filteredAnswers.json();
            error = "";
        } catch(err) {
            error = err.message;
        } finally {
            loading = false;
        }
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
    {#if consultation}
        <QuestionCard
            clickable={true}
            consultationId={consultation?.id}
            question={consultation?.questions.find(question => question.id === questionId)}
        />
    {:else}
        <p transition:slide>Loading consultation</p>
    {/if}
</section>