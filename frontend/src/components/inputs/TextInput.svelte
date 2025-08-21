<script lang="ts">
    import clsx from "clsx";

    import { fade } from "svelte/transition";

    import Button from "./Button.svelte";
    import MaterialIcon from "../MaterialIcon.svelte";
    import Close from "../svg/material/Close.svelte";

    export let id: string = "";
    export let label: string = "";
    export let hideLabel: boolean = false;
    export let value: string = "";
    export let placeholder: string = "";
    export let setValue = (newValue: string) => {};

    export let variant: "default" | "search" = "default";
</script>

<div class="relative">
    <label
        for={id}
        class={clsx([
            hideLabel && "sr-only",
        ])}
    >
        {label}
    </label>
    <input
        class={clsx([
            "w-full",
            "p-1",
            "border",
            "border-gray-300",
            "rounded-sm",
            "focus:outline-2",
            "focus:outline-yellow-300",
            variant === "search" && "pr-4",
        ])}
        type="text"
        id={id}
        placeholder={placeholder}
        value={value}
        on:input={(e) => setValue((e.target as HTMLInputElement).value)}
    />

    {#if variant === "search" && value}
        <div
            transition:fade={{duration: 200}}
            class={clsx([
                "absolute",
                "right-1",
                "top-1/2",
                "-translate-y-1/2",
            ])}
        >
            <Button variant="ghost" handleClick={() => setValue("")}>
                <MaterialIcon size="1.3rem" color="black">
                    <Close />
                </MaterialIcon>
            </Button>
        </div>
    {/if}
</div>