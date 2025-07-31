<script lang="ts">
    import clsx from "clsx";

    import { slide } from "svelte/transition";

    import Button from "./inputs/Button.svelte";


    export let magicLink = "";

    let error = "";

    const handleSubmit = async () => {
        error = "";

        if (!magicLink) {
            error = "No magic link found";
        }
        try {
            fetch("/api/magic-link", {
                method: "POST",
                body: JSON.stringify({
                    token: magicLink,
                }),
                headers: {
                    "Content-Type": "application/json",
                }
            })
        } catch(err) {
            error = err.message;
        }
    }
</script>

<div class="mt-4">
    <Button variant="primary" handleClick={handleSubmit}>
        Sign in
    </Button>

    {#if error}
        <small
            transition:slide={{ duration: 300 }}
            class={clsx([
                "text-sm",
                "text-red-500",
            ])}
        >
            {error}
        </small>
    {/if}
</div>