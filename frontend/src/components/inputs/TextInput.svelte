<script lang="ts">
    import clsx from "clsx";

    export let id: string = "";
    export let label: string = "";
    export let hideLabel: boolean = false;
    export let value: string = "";
    export let placeholder: string = "";
    export let setValue = () => {};
</script>

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
    ])}
    type="text"    
    id={id}
    placeholder={placeholder}
    value={value}
    on:input={setValue}
/>