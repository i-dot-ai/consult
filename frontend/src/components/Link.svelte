<script lang="ts">
    import clsx from "clsx";

    export let href: string = "";
    export let title: string = "";
    export let ariaLabel: string = "";
</script>

<a
    class={clsx([
        "transition-colors",
        "duration-300",
        "text-primary",
        "hover:underline",
    ])}
    href={href}
    aria-label={ariaLabel}
    title={title}
>
    <slot />
</a>