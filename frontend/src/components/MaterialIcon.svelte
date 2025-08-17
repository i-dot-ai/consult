<script>
    export let color = "fill-white";
    export let hoverColor = null;
    export let size = "1rem";

    let hovering = false;
</script>

<svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 -960 960 960"
    class={hoverColor && hovering ? hoverColor : color}
    on:mouseenter={() => hovering = true}
    on:mouseleave={() => hovering = false}
    role="img"
>
    <slot />
</svg>