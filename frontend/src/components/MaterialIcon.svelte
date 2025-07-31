<script>
    export let color = "black";
    export let size = "1rem";
</script>

<svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 -960 960 960"
    fill={color}
>
    <slot />
</svg>