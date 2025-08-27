<script lang="ts">
    import MaterialIcon from "../MaterialIcon.svelte";
    import Search from "../svg/material/Search.svelte";

    let {
        title = "",
        body = "",
    } = $props();
</script>

<div class="flex justify-center items-center flex-col my-16">
    <MaterialIcon color="fill-neutral-200" size="4rem">
        <Search />
    </MaterialIcon>

    <p class="text-xl">{title}</p>
    <p class="text-neutral-600">{body}</p>
</div>