<script lang="ts">
    import MaterialIcon from "../MaterialIcon.svelte";
    import Help from "../svg/material/Help.svelte";
    import Star from "../svg/material/Star.svelte";
    import Panel from "./Panel.svelte";

    interface Question {
        title: string;
    }
    interface Consultation {
        questions: Array<Question>;
    }

    export let consultation: Consultation;
</script>

<Panel>
    {#each consultation.questions as question}
        <Panel>
            <div class="flex gap-2 items-start">
                <div class="mt-0.5">
                    <MaterialIcon size="1.3rem" color="teal">
                        <Help />
                    </MaterialIcon>
                </div>
                <div class="grow">
                    <p class="text-md">
                        {question.title}
                    </p>
                </div>
                <div class="mt-0.5">
                    <MaterialIcon size="1.3rem" color="teal">
                        <Star />
                    </MaterialIcon>
                </div>
            </div>
        </Panel>
    {/each}
</Panel>