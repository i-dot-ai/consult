<script lang="ts">
    import clsx from "clsx";

    import { slide } from "svelte/transition";

    import { Routes } from "../global/enums.ts"

    import Button from "./inputs/Button.svelte";

    export let magicLink = "";

    let error = "";

    const handleSubmit = async () => {
        error = "";

        if (!magicLink) {
            error = "No magic link found";
        }
        try {
            const response = await fetch("/api/astro/magic-link", {
                method: "POST",
                body: JSON.stringify({
                    token: magicLink,
                }),
                headers: {
                    "Content-Type": "application/json",
                }
            })

            if (!response.ok) {
                error = "Response failed";
                return;
            }

            window.location.href = Routes.Home;
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