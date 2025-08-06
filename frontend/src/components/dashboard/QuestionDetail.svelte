<script lang="ts">
    import clsx from "clsx";

    import MaterialIcon from "../MaterialIcon.svelte";
    import Button from "../inputs/Button.svelte";
    import Panel from "../dashboard/Panel.svelte";
    import Star from "../svg/material/Star.svelte";
    import SearchCard from "./SearchCard.svelte";

    import { getConsultationDetailUrl } from "../../global/routes.ts";

    export let consultationId: string = "";
    export let questionTitle: string = "";
    
    let _responsesTotal: number = 0;
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
    <Panel>
        <SearchCard title={questionTitle}>
            <Button
                slot="aside"
                variant={"ghost"}
                handleClick={() => {}}
            >
                <MaterialIcon size={"1.3rem"}>
                    <Star />
                </MaterialIcon>
            </Button>

            <div slot="footer">
                <small class={clsx([
                    "flex",
                    "items-center",
                ])}>
                    {_responsesTotal.toLocaleString()} responses
                </small>
            </div>
        </SearchCard>
    </Panel>
</section>