<script lang="ts">
  import Button from "../inputs/Button/Button.svelte";
  import Select from "../inputs/Select/Select.svelte";

  interface Props {
    id: string;
    totalItems: number;
    currentPage: number;
    pageSize: number;
    pageSizes?: number[];
    label?: string;
    onPageChange: (page: number) => void;
    onPageSizeChange: (pageSize: number) => void;
  }

  let {
    id,
    totalItems,
    currentPage,
    pageSize,
    pageSizes = [10, 25, 50],
    label = "Pagination",
    onPageChange,
    onPageSizeChange,
  }: Props = $props();

  let totalPages = $derived(Math.max(1, Math.ceil(totalItems / pageSize)));
  let firstItem = $derived(
    totalItems === 0 ? 0 : (currentPage - 1) * pageSize + 1,
  );
  let lastItem = $derived(Math.min(currentPage * pageSize, totalItems));

  // The first page, the last page and the current page's neighbours; the rest collapse into gaps.
  let pageNumbers = $derived.by(() => {
    const numbers: (number | "gap")[] = [];
    for (let page = 1; page <= totalPages; page += 1) {
      const nearCurrent = Math.abs(page - currentPage) <= 1;
      if (page === 1 || page === totalPages || nearCurrent) {
        numbers.push(page);
      } else if (numbers[numbers.length - 1] !== "gap") {
        numbers.push("gap");
      }
    }
    return numbers;
  });

  function changePageSize(value: string | undefined) {
    if (value === undefined) {
      return;
    }
    onPageSizeChange(Number.parseInt(value));
  }
</script>

<div
  class="pagination flex flex-wrap items-center justify-between gap-4 border-t border-neutral-200 pt-4"
>
  <p
    class="text-sm text-neutral-500"
    data-testid="visible-items-text"
    aria-live="polite"
  >
    Showing {firstItem} to {lastItem} of {totalItems}
  </p>

  <nav aria-label={label} class="flex flex-wrap items-center gap-1">
    <Button
      variant="ghost"
      size="sm"
      disabled={currentPage === 1}
      ariaLabel="Previous page"
      handleClick={() => onPageChange(currentPage - 1)}
    >
      ‹
    </Button>

    {#each pageNumbers as pageNumber, index (index)}
      {#if pageNumber === "gap"}
        <span class="px-1 text-sm text-neutral-400" aria-hidden="true">…</span>
      {:else}
        <Button
          variant={pageNumber === currentPage ? "gray" : "ghost"}
          size="sm"
          ariaLabel={`Page ${pageNumber}`}
          ariaCurrent={pageNumber === currentPage ? "page" : undefined}
          testId={pageNumber === currentPage ? "current-page" : ""}
          handleClick={() => onPageChange(pageNumber)}
        >
          {pageNumber}
        </Button>
      {/if}
    {/each}

    <Button
      variant="ghost"
      size="sm"
      disabled={currentPage === totalPages}
      ariaLabel="Next page"
      handleClick={() => onPageChange(currentPage + 1)}
    >
      ›
    </Button>
  </nav>

  <div class="page-size">
    <Select
      id={`${id}-page-size-select`}
      label={{ text: "Per page", horizontal: true }}
      items={pageSizes.map((size) => ({
        value: size.toString(),
        label: size.toString(),
      }))}
      value={pageSize.toString()}
      onchange={changePageSize}
    />
  </div>
</div>

<style>
  @reference "../../styles/global.css";

  .pagination :global(nav button) {
    @apply h-8 min-w-8 justify-center rounded-md px-2 text-sm;
  }

  .page-size :global(label) {
    @apply text-sm text-neutral-500;
  }

  .page-size :global(select) {
    @apply h-8 w-auto rounded-md border-neutral-500 px-2 py-0 text-sm;
  }
</style>
