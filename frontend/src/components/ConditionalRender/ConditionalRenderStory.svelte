<script lang="ts">
    import Link from "../Link.svelte";
    import Title from "../Title.svelte";
    import ConditionalRender from "./ConditionalRender.svelte";
</script>

<div>
    <Title level={2} text="With Condition True" />
    <ConditionalRender condition={true} element={"a"} href="#">
        <p>Slot text</p>
    </ConditionalRender>
</div>

<div>
    <Title level={2} text="With Condition False" />
    <ConditionalRender condition={false} element={"a"} href="#">
        <p>Slot text</p>
    </ConditionalRender>
</div>

<div>
    <Title level={2} text="With Link Element" />
    <ConditionalRender condition={true} element={Link} href="#">
        <p>Slot text</p>
    </ConditionalRender>
</div>