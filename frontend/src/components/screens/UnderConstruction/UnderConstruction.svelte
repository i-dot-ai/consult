<script lang="ts">
    import MaterialIcon from "../../MaterialIcon.svelte";
    import Warning from "../../svg/material/Warning.svelte";
    import Title from "../../Title.svelte";
</script>

<div class="flex flex-col gap-2 justify-center items-center mt-36">
    <div class="mb-4">
        <MaterialIcon color="fill-neutral-500" size="3rem">
            <Warning />
        </MaterialIcon>
    </div>

    <Title level={2}>Under Construction</Title>
    <p class="text-neutral-500">This functionality is currently under construction</p>
</div>