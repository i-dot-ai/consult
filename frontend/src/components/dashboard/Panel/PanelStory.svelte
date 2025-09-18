<script lang="ts">
    import Switch from "../../inputs/Switch/Switch.svelte";
    import TextInput from "../../inputs/TextInput/TextInput.svelte";
    import Title from "../../Title.svelte";
    import Panel from "./Panel.svelte";


    let bg = $state(true);
    let border = $state(true);
    let level = $state(1);
    let content = $state("<p>Panel test content</p>");
</script>

<Title level={2} text="No Background" />
<Panel
    border={true}
    bg={false}
    level={1}
>
    <p>No background example</p>
</Panel>

<Title level={2} text="No Border" />
<Panel
    border={false}
    bg={true}
    level={1}
>
    <p>No background example</p>
</Panel>

<Title level={2} text="Nested" />
<Panel
    border={true}
    bg={false}
    level={1}
>
    <Panel
        border={true}
        bg={false}
        level={2}
    >
        <Panel
            border={true}
            bg={true}
            level={3}
        >
            <p class="text-xs px-2 my-2">Nested Panel Example</p>
        </Panel>
    </Panel>
</Panel>

<Title level={2} text="Dynamic" />
<Panel
    border={border}
    bg={bg}
    level={level}
>
    {@html content}
</Panel>

<hr class="my-8" />

<div class="w-max">
    <Switch
        id="border-input"
        label="Border"
        value={border}
        handleChange={(newVal) => border = newVal}
    />
</div>

<div class="w-max">
    <Switch
        id="bg-input"
        label="Background"
        value={bg}
        handleChange={(newVal) => bg = newVal}
    />
</div>

<TextInput
    id="input-level"
    label="Level"
    value={level.toString()}
    setValue={(newValue) => level = parseInt(newValue)}
/>

<TextInput
    id="input-content"
    label="Content"
    value={content}
    setValue={(newValue) => content = newValue}
/>