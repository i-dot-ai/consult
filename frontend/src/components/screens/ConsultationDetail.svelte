<script lang="ts">
    import { onMount } from "svelte";
    import { slide } from "svelte/transition";

    import Title from "../Title.svelte";
    import Link from "../Link.svelte";
    import QuestionList from "../dashboard/QuestionList.svelte";
    import TextInput from "../inputs/TextInput.svelte";
    import TitleRow from "../dashboard/TitleRow.svelte";
    import Help from "../svg/material/Help.svelte";
    import Star from "../svg/material/Star.svelte";

    import type { Question, Consultation } from "../../global/types.ts";
    import { getConsultationDetailUrl, getApiConsultationUrl } from "../../global/routes.ts";
    import { favStore } from "../../global/stores.ts";
    import Panel from "../dashboard/Panel.svelte";

    export let consultationId: string = "";

    let searchValue: string = "";
    let consultation: Consultation;
    let loading: boolean = true;
    let error: string = "";

    onMount(async () => {
        try {
            const response = await fetch(getApiConsultationUrl(consultationId));
            if (!response.ok) {
                error = "Response not ok";
                return;
            }
            const consultationData = await response.json();
            consultation = consultationData;
            error = "";
        } catch(err: any) {
            error = err.message;
        } finally {
            loading = false;
        }
    })
</script>


<section transition:slide class="my-8">
    <div class="my-2">
        <TitleRow title="Favourited questions">
            <Star slot="icon" />
        </TitleRow>
    </div>

    {#if $favStore.length > 0}
        {#if loading}
            <p transition:slide>Loading questions...</p>
        {:else if error}
            <p transition:slide>{error}</p>
        {:else}
            <div transition:slide>
                <div class="mb-8">
                    <QuestionList
                        consultationId={consultation.id}
                        questions={consultation.questions
                            .filter(question => $favStore.includes(question.id))
                        }
                        highlightText={searchValue}
                    />
                </div>
            </div>
        {/if}
    {:else}
        <p transition:slide>You have not favourited any question.</p>
    {/if}
</section>

<section class="my-8">
    <div class="my-2">
        <TitleRow
            title="All consultation questions"
            subtitle="Browse or search through all questions in this consultation."
        >
            <Help slot="icon" />

            <p slot="aside">
                {consultation?.questions?.length || 0} questions
            </p>
        </TitleRow>
    </div>

    <Panel bg={true} border={true}>
        {#if loading}
            <p transition:slide>Loading questions...</p>
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

                <div class="mb-4">
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
            </div>
        {/if}
    </Panel>
</section>