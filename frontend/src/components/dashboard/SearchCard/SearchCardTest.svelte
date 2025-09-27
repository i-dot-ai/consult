<script lang="ts">
  import SearchCard from "./SearchCard.svelte";

  interface Props {
    asideContent: string;
    footerContent: string;
    title: string;
    description: string;
    tags: string[];
    highlightText: string;
  }

  let {
    asideContent,
    footerContent,
    title,
    description,
    tags,
    highlightText,
  }: Props = $props();
</script>

<SearchCard {title} {description} {tags} {highlightText}>
  <p slot="aside">{asideContent}</p>
  <p slot="footer">{footerContent}</p>
</SearchCard>
