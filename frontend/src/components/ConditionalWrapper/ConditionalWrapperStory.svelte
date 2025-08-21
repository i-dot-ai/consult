<script lang="ts">
    import Link from "../Link.svelte";
    import Title from "../Title.svelte";
    import ConditionalWrapper from "./ConditionalWrapper.svelte";
</script>

<div>
    <Title level={2} text="With Condition True" />
    <ConditionalWrapper condition={true} element={"a"} href="#">
        <p>Slot text</p>
    </ConditionalWrapper>
</div>

<div>
    <Title level={2} text="With Condition False" />
    <ConditionalWrapper condition={false} element={"a"} href="#">
        <p>Slot text</p>
    </ConditionalWrapper>
</div>

<div>
    <Title level={2} text="With Link Element" />
    <ConditionalWrapper condition={true} element={Link} href="#">
        <p>Slot text</p>
    </ConditionalWrapper>
</div>