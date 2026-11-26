<script>
  import Button from "./Button.svelte";

  let {
    variant,
    highlighted,
    highlightVariant,
    disabled,
    handleClick,
    children,
  } = $props();
</script>

<Button
  {variant}
  {highlighted}
  {highlightVariant}
  {disabled}
  {handleClick}
>
  {@render children()}
</Button>