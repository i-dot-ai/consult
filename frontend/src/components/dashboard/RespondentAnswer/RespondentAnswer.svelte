<script lang="ts">
    import clsx from "clsx";

    import Panel from "../../dashboard/Panel/Panel.svelte";
    import Tag from "../../Tag/Tag.svelte";
    import MaterialIcon from "../../MaterialIcon.svelte";
    import Diamond from "../../svg/material/Diamond.svelte";
    import { getQuestionDetailUrl } from "../../../global/routes";


    interface Props {
        consultationId: string;
        questionId: string;
        questionTitle: string;
        questionNumber: number;
        answerText: string;
        themes: string[];
        evidenceRich: boolean;
    }

    let {
        consultationId = "",
        questionId = "",
        questionTitle = "",
        questionNumber = 0,
        answerText = "",
        themes = [],
        evidenceRich = false,
    }: Props = $props();
</script>

<style lang="scss">
    a:hover {
        h3 {
            color: var(--color-primary);
        }
        .question-number {
            color: white;
            background-color: var(--color-primary);
        }
    }
</style>

<Panel border={true} bg={true}>
    <article>
        <header class="flex flex-col-reverse md:flex-row gap-y-4 justify-between items-start gap-2">
            <a href={getQuestionDetailUrl(consultationId, questionId)}>
                <div class="flex items-start gap-2">
                    <div class={clsx([
                        "question-number",
                        "p-1",
                        "rounded-lg",
                        "border",
                        "border-neutral-200",
                        "text-xs",
                        "bg-neutral-100",
                        "transition-colors",
                    ])}>
                        Q{questionNumber}
                    </div>

                    <h3 class={clsx([
                        "text-xs",
                        "text-neutral-500",
                        "transition-colors",
                        "mt-0.5",
                    ])}>
                        {questionTitle}
                    </h3>
                </div>
            </a>

            <div class="whitespace-nowrap">
                {#if evidenceRich}
                    <Tag variant="warning">
                        <MaterialIcon size="0.9rem" color="fill-yellow-600">
                            <Diamond />
                        </MaterialIcon>

                        <span class="text-xs">Evidence-rich</span>
                    </Tag>
                {/if}
            </div>
        </header>

        <p class="text-sm my-4">
            {answerText}
        </p>

        <footer class="flex items-center flex-wrap gap-2">
            <small class="text-xs text-neutral-500">
                Themes:
            </small>

            {#each themes as theme}
                <Tag variant="dark">
                    {theme}
                </Tag>
            {/each}
        </footer>
    </article>
</Panel>