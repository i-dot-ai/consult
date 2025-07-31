<script lang="ts">
    import Button from "./inputs/Button.svelte";
    
    export let magicLink = "";
</script>

<div class="mt-4">
    <Button
        variant="primary"
        handleClick={() => {
            window.location.href = "/" + magicLink;
        }}
    >
        Sign in
    </Button>
</div>