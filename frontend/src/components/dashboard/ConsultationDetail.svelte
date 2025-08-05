<script lang="ts">
    import { onMount } from "svelte";
    import { slide } from "svelte/transition";

    import Title from "../Title.svelte";
    import Link from "../Link.svelte";
    import QuestionList from "./QuestionList.svelte";
    import TextInput from "../inputs/TextInput.svelte";
    
    import type { Question, Consultation } from "../../global/types.ts";
    import { getConsultationDetailUrl } from "../../global/enums.ts";


    export let consultationId: string = "";

    let searchValue: string = "";
    let consultation: Consultation;
    let loading: boolean = true;
    let error: string = "";

    onMount(async () => {
        try {
            const response = await fetch(`/api/consultations/${consultationId}`);
            if (!response.ok) {
                error = "Response not ok";
                loading = false;
                return;
            }
            const consultationData = await response.json();
            consultation = consultationData;
            loading = false;
            error = "";
        } catch(err) {
            error = err.message;
        }
    })
</script>

<section class="mt-4">
    {#if loading}
        <p transition:slide>Loading consultation...</p>
    {:else if error}
        <p transition:slide>{error}</p>
    {:else}
        <div transition:slide>
            <TextInput
                variant="search"
                id="search-input"
                label="Search"
                placeholder="Search..."
                hideLabel={true}
                value={searchValue}
                setValue={(value) => searchValue = value.trim()}
            />

            <QuestionList
                consultationId={consultation.id}
                questions={consultation.questions.filter(question => {
                    return (
                        `Q${question.number}: ${question.question_text}`
                        .toLocaleLowerCase()
                        .includes(searchValue.toLocaleLowerCase())
                    )
                })}
                highlightText={searchValue}
            />
        </div>
    {/if}
</section>