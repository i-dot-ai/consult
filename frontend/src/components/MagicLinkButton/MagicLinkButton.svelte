<script lang="ts">
    import { slide } from "svelte/transition";

    import { Routes } from "../../global/routes";

    import Button from "../inputs/Button/Button.svelte";
    import Alert from "../Alert.svelte";


    const validateMagicLink = async () => {
        loading = true;
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
        } catch(err: any) {
            error = err.message;
        } finally {
            loading = false;
        }
    }

    export let magicLink = "";

    let loading = false;
    let error = "";
</script>

<div class="mt-4">
    <Button variant="primary" disabled={loading} handleClick={validateMagicLink}>
        {loading ? "Signing in..." : "Sign in"}
    </Button>

    {#if error}
        <div class="mt-2" transition:slide={{ duration: 300 }}>
            <Alert>
                {error}
            </Alert>
        </div>
    {/if}
</div>