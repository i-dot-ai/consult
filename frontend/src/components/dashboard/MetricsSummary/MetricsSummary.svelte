<script lang="ts">
    import { type Component } from "svelte";

    import MaterialIcon from "../../MaterialIcon.svelte";
    import Description from "../../svg/material/Description.svelte";
    import Group from "../../svg/material/Group.svelte";
    import Shield from "../../svg/material/Shield.svelte";


    interface Props {
        questionCount: number;
        responseCount: number;
        demoCount: number;
    }

    let {
        questionCount = 0,
        responseCount = 0,
        demoCount = 0,
    }: Props = $props();
</script>

{#snippet row(text: string, count: number, icon: Component)}
    <div class="flex items-center justify-between my-2">
        <div class="flex items-center">
            <MaterialIcon color="fill-neutral-500">
                <svelte:component this={icon} />
            </MaterialIcon>

            <span class="ml-2 text-sm text-neutral-700">
                {text}
            </span>
        </div>

        <span class="text-xl font-bold">
            {count.toLocaleString()}
        </span>
    </div>
{/snippet}

{@render row( "Responses", questionCount, Description )}
{@render row( "Questions", responseCount, Group )}
{@render row( "Demographics",  demoCount, Shield )}