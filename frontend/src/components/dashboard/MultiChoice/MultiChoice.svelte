<script lang="ts">
    import clsx from "clsx";

    import { fade } from "svelte/transition";

    import { getPercentage } from "../../../global/utils";

    import Progress from "../../Progress/Progress.svelte";
    import Panel from "../Panel/Panel.svelte";
    import TitleRow from "../TitleRow.svelte";
    import List from "../../svg/material/List.svelte";


    export interface MultiChoiceAnswer {
        answer?: string;
        response_count: number;
    }
    interface Props {
        data: MultiChoiceAnswer[];
    }

    let {
        data = [],
    }: Props = $props();
</script>

<section class="my-4" transition:fade>
    <Panel border={true}>
        <TitleRow
            level={2}
            title="Multiple Choice Answers"
        >
            <List slot="icon" />
        </TitleRow>

        {@const total = data.map(item => item.response_count).reduce(
            (acc, curr) => acc + curr, 0,
        )}
        <Panel bg={true}>
            {#each data as item, i (i)}
                {@const percentage = getPercentage(item.response_count, total)}

                <div  class={clsx([
                    "flex",
                    "items-center",
                    "justify-between",
                    "gap-2",
                    "text-xs",
                    "mb-4",
                    "last:mb-0",
                ])}>
                    <h3 class="w-1/2">
                        {item.answer}
                    </h3>
                    
                    <div class={clsx([
                        "flex",
                        "flex-col",
                        "justify-center",
                        "items-center",
                        "gap-1",
                        "w-2/3",
                        "sm:flex-row",
                        "sm:w-1/2",
                        "sm:gap-4",
                    ])}>
                        <div class={clsx([
                            "flex",
                            "justify-between",
                            "items-center",
                            "w-full",
                            "sm:justify-end",
                        ])}>
                            <span>{percentage}%</span>

                            <span class="sm:hidden">
                                {item.response_count}
                            </span>
                        </div>
                        <div class="w-full">
                            <Progress value={percentage} />
                        </div>
                        
                        <span class="hidden sm:block">
                            {item.response_count}
                        </span>
                    </div>
                </div>
            {/each}
        </Panel>
    </Panel>
</section>