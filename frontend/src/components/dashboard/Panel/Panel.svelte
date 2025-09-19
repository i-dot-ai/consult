<script>
    import clsx from "clsx";

    let {
        border = true,
        bg = false,
        level = 1,
        children,
    } = $props();
</script>

<div
    data-testid="panel-component"
    class={clsx([
        "h-full",
        "my-4",
        level === 1 && "p-4",
        level === 2 && "p-2",
        level === 3 && "p-1",
        "rounded-2xl",
        border && "border",
        border && "border-gray-200",
        bg && "bg-neutral-50",
    ])}
>
    {@render children()}
</div>