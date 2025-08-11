<script lang="ts">
    import Star from "../svg/material/Star.svelte";
    import Panel from "./Panel.svelte";
    import TitleRow from "./TitleRow.svelte";
    import ThemesTable from "./ThemesTable.svelte";

    export let themes = [];
    export let totalAnswers: number = 0;
    let sortAscending: boolean = true;
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
            subtitle={`Total themes ${themes?.length || 0}`}
        >
            <Star slot="icon" />
        </TitleRow>

        <ThemesTable
            themes={themes}
            totalAnswers={totalAnswers}
        />
    </Panel>
</section>