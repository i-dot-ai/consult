<script lang="ts">
    import Star from "../svg/material/Star.svelte";
    import Panel from "./Panel.svelte";
    import TitleRow from "./TitleRow.svelte";

    export let themes = [];
</script>

<section class="my-4">
    <Panel>
        <TitleRow
            level={2}
            title="Demographics"
            subtitle="Demographic breakdown for this question"
        >
            <Star slot="icon" />
        </TitleRow>
    </Panel>
</section>

<section class="my-4">
    <Panel>
        <TitleRow
            level={2}
            title="Theme analysis"
            subtitle={`Total themes ${themes.length}`}
        >
            <Star slot="icon" />
        </TitleRow>
    </Panel>
</section>