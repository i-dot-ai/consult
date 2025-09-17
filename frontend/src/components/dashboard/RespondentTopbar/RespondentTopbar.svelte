<script lang="ts">
    import clsx from "clsx";

    import Button from "../../inputs/Button/Button.svelte";
    import MaterialIcon from "../../MaterialIcon.svelte";
    import ArrowForward from "../../svg/material/ArrowForward.svelte";
    import ChevronRight from "../../svg/material/ChevronRight.svelte";


    interface Props {
        respondentId: string;
    }

    let {
        respondentId = "",
    }: Props = $props();
</script>

<div class={clsx([
    "flex",
    "items-center",
    "justify-center",
    "md:justify-between",
    "flex-wrap",
    "gap-4",
    "mb-4",
])}>
    <div class="flex items-center gap-4">
        <div class="m-auto">
            <Button size="xs" variant="ghost">
                <div class="rotate-180">
                    <MaterialIcon color="fill-neutral-700">
                        <ArrowForward />
                    </MaterialIcon>
                </div>

                <span>Back to Analysis</span>
            </Button>
        </div>

        <h1 class="font-bold text-lg">Respondent {respondentId}</h1>
    </div>

    <div class="flex items-center gap-4">
        <Button size="xs">
            <div class="rotate-180">
                <MaterialIcon color="fill-neutral-700">
                    <ChevronRight />
                </MaterialIcon>
            </div>

            <span class="mr-2 my-[0.1rem]">Previous Respondent</span>
        </Button>

        <Button size="xs">
            <span class="ml-2 my-[0.1rem]">Next Respondent</span>

            <MaterialIcon color="fill-neutral-700">
                <ChevronRight />
            </MaterialIcon>
        </Button>
    </div>
</div>