<script lang="ts" module>
  export type SortDirection = "asc" | "desc";

  export type SortState<T> = {
    key: keyof T & string;
    direction: SortDirection;
  };

  export type DataTableColumn<T> = {
    key: keyof T & string;
    label: string;
    sortable?: boolean;
    hidden?: boolean;
    columnSelect?: boolean;
    width?: string;
    align?: "left" | "center" | "right";
    sortValue?: (row: T) => unknown;
    filterValue?: (row: T) => string;
  };
</script>

<script lang="ts" generics="T extends Record<string, unknown>">
  import clsx from "clsx";

  import { type Snippet } from "svelte";

  import MaterialIcon from "../MaterialIcon.svelte";
  import ArrowForward from "../svg/material/ArrowForward.svelte";
  import SwapVert from "../svg/material/SwapVert.svelte";
  import LoadingIndicator from "../LoadingIndicator/LoadingIndicator.svelte";
  import TextInput from "../inputs/TextInput/TextInput.svelte";
  import Select from "../inputs/Select/Select.svelte";
  import Button from "../inputs/Button/Button.svelte";
  import SearchableSelect from "../inputs/SearchableSelect.svelte";

  type Props = {
    rows?: T[];
    columns: DataTableColumn<T>[];
    caption?: string;
    loading?: boolean;
    sortable?: boolean;
    initialSort?: SortState<T>;
    searchable?: boolean;
    searchPlaceholder?: string;
    paginated?: boolean;
    pageSizes?: number[];
    columnSelect?: boolean;
    onSortChange?: (sort: SortState<T> | null) => void;
    onRowClick?: (row: T) => void;
  };

  let {
    rows = [],
    columns,
    caption = "Data table",
    loading = false,
    sortable = true,
    initialSort,
    searchable = true,
    searchPlaceholder,
    paginated = true,
    pageSizes = [10, 50, 100, 250, 500],
    columnSelect = true,
    onSortChange,
    onRowClick,
  }: Props = $props();

  let sort = $derived<SortState<T> | null>(initialSort ?? null);

  let announcement = $state("");

  let searchQuery = $state("");

  let currentPage = $derived.by(() => {
    // set currentPage back to 1 if pageSizes or searchQuery change
    // eslint-disable-next-line @typescript-eslint/no-unused-expressions
    pageSizes && searchQuery;
    return 1;
  });

  let pageSize = $derived(pageSizes[0]);

  const visibleColumns = $derived(columns.filter((column) => !column.hidden));

  const sortedRows = $derived.by(() => {
    if (!sort) {
      return rows;
    }

    const column = visibleColumns.find((column) => column.key === sort?.key);

    if (!column) {
      return rows;
    }

    return [...rows].sort((a, b) => {
      const aValue = getSortValue(a, column);
      const bValue = getSortValue(b, column);

      const result = compareValues(aValue, bValue);

      return sort?.direction === "asc" ? result : -result;
    });
  });

  const filteredRows = $derived.by(() => {
    const searchableColumns = visibleColumns.filter((column) => {
      return column.filterValue !== undefined || column.hidden !== true;
    });

    return sortedRows.filter((row) => {
      return searchableColumns.some((column) => {
        const value = column.filterValue?.(row) ?? row[column.key];
        return String(value ?? "")
          .toLocaleLowerCase()
          .includes(searchQuery.trim().toLocaleLowerCase());
      });
    });
  });

  const totalRows = $derived(filteredRows.length);
  const totalPages = $derived(
    paginated ? Math.max(1, Math.ceil(totalRows / pageSize)) : 1,
  );
  const paginatedRows = $derived(
    paginated
      ? filteredRows.slice((currentPage - 1) * pageSize, currentPage * pageSize)
      : filteredRows,
  );

  function setPage(page: number) {
    currentPage = Math.min(Math.max(page, 1), totalPages);
    announcement = `Page ${currentPage} of ${totalPages}`;
  }

  function getSortValue(row: T, column: DataTableColumn<T>) {
    return column.sortValue ? column.sortValue(row) : row[column.key];
  }

  function compareValues(a: unknown, b: unknown): number {
    if (a === b) {
      return 0;
    }
    if (a == null) {
      return -1;
    }
    if (b == null) {
      return 1;
    }

    // Compare numbers
    if (typeof a === "number" && typeof b === "number") {
      return a - b;
    }

    // Compare dates
    if (a instanceof Date && b instanceof Date) {
      return a.getTime() - b.getTime();
    }

    // Compare strings
    return String(a).localeCompare(String(b), undefined, {
      numeric: true,
      sensitivity: "base",
    });
  }

  function isSortable(column: DataTableColumn<T>) {
    return sortable && column.sortable === true;
  }

  function isSortApplied(
    column: DataTableColumn<T>,
    sort: SortState<T> | null,
  ) {
    return sort && sort.key === column.key;
  }

  function sortBy(column: DataTableColumn<T>) {
    if (!isSortable(column)) {
      return;
    }

    if (!isSortApplied(column, sort)) {
      sort = {
        key: column.key,
        direction: "asc",
      };
    } else if (sort!.direction === "asc") {
      sort = {
        key: column.key,
        direction: "desc",
      };
    } else if (sort!.direction === "desc") {
      sort = null;
    }

    onSortChange?.(sort);

    announcement =
      `${column.label} sorted ` +
      `${sort?.direction === "asc" ? "ascending" : "descending"}`;
  }

  function getSortAriaLabel(column: DataTableColumn<T>) {
    if (!isSortable(column)) {
      return undefined;
    }

    if (!isSortApplied(column, sort)) {
      return `Sort by ${column.label}`;
    }

    return sort!.direction === "asc"
      ? `Sorted ascending by ${column.label}. Click to sort descending.`
      : `Sorted descending by ${column.label}. Click to sort ascending.`;
  }

  function getSortText(column: DataTableColumn<T>, sort: SortState<T> | null) {
    if (sort?.key !== column.key) {
      return "none";
    }
    if (sort.direction === "asc") {
      return "ascending";
    }
    return "descending";
  }
</script>

<div class="w-full">
  <div class="sr-only" aria-live="polite" aria-atomic="true">
    {announcement}
  </div>

  <div
    class={clsx([
      "flex",
      "justify-between",
      "items-center",
      "gap-2",
      "pb-4",
      "pt-2",
    ])}
  >
    {#if columnSelect}
      <SearchableSelect
        id="visible-columns-select"
        label="Visible columns"
        options={columns.map((column) => ({
          value: column.key,
          label: column.label,
        }))}
        hideLabel={true}
        placeholder={`${visibleColumns.length} columns visible`}
        selectedValues={visibleColumns.map((column) => column.key)}
        handleChange={(newVal) => {
          columns = columns.map((column) => ({
            ...column,
            hidden:
              newVal.value === column.key ? !column.hidden : column.hidden,
          }));
        }}
      />
    {/if}

    {#if searchable}
      <div class={clsx(["w-1/3", "ml-auto", "text-sm"])}>
        <TextInput
          id="search-input"
          label="Search"
          hideLabel={true}
          variant="search"
          value={searchQuery}
          setValue={(newValue) => (searchQuery = newValue)}
          placeholder={searchPlaceholder || "Search..."}
        />
      </div>
    {/if}
  </div>

  <div
    class={clsx([
      "overflow-x-auto",
      "rounded-lg",
      "border",
      "border-neutral-200",
      "bg-white",
    ])}
  >
    <table class={clsx(["min-w-full", "divide-y", "divide-neutral-200"])}>
      {#if caption}
        <caption class="sr-only">
          {caption}
        </caption>
      {/if}

      <thead class="bg-neutral-50">
        <tr>
          {#each visibleColumns as column (column.key)}
            <th
              scope="col"
              class={clsx([
                "px-4",
                "py-3",
                "text-left",
                "text-xs",
                "font-[500]",
                "tracking-wide",
                "text-neutral-600",
                column.align === "center" && "text-center",
                column.align === "right" && "text-right",
              ])}
              aria-sort={getSortText(column, sort)}
              data-testid="column-header"
            >
              {#if sortable && column.sortable !== false}
                <Button
                  variant="ghost"
                  justify="left"
                  size="xs"
                  ariaLabel={getSortAriaLabel(column)}
                  handleClick={() => sortBy(column)}
                  highlighted={sort?.key === column.key}
                  highlightVariant="none"
                >
                  <span>
                    {column.label}
                  </span>

                  <span aria-hidden="true" class="text-neutral-400">
                    {#if sort?.key === column.key && sort.direction === "asc"}
                      <div class="rotate-90">
                        <MaterialIcon color="fill-neutral-500">
                          <ArrowForward />
                        </MaterialIcon>
                      </div>
                    {:else if sort?.key === column.key && sort.direction === "desc"}
                      <div class="rotate-270">
                        <MaterialIcon color="fill-neutral-500">
                          <ArrowForward />
                        </MaterialIcon>
                      </div>
                    {:else}
                      <MaterialIcon color="fill-neutral-500">
                        <SwapVert />
                      </MaterialIcon>
                    {/if}
                  </span>
                </Button>
              {:else}
                <span>{column.label}</span>
              {/if}
            </th>
          {/each}
        </tr>
      </thead>

      {#snippet messageRow(content: Snippet)}
        <tr>
          <td
            colspan={visibleColumns.length}
            class={clsx([
              "px-4",
              "py-12",
              "text-center",
              "text-sm",
              "text-neutral-500",
            ])}
          >
            {@render content()}
          </td>
        </tr>
      {/snippet}

      {#snippet loadingMessage()}
        <span role="status">
          <LoadingIndicator size="3rem" />
        </span>
      {/snippet}

      {#snippet noDataMessage()}
        <span>No data available</span>
      {/snippet}

      <tbody class="divide-y divide-neutral-200">
        {#if loading}
          {@render messageRow(loadingMessage)}
        {:else if paginatedRows.length === 0}
          {@render messageRow(noDataMessage)}
        {:else}
          {#each paginatedRows as row, i (i)}
            <tr
              class={clsx([
                "transition-colors",
                "hover:bg-neutral-50",
                Boolean(onRowClick) && "cursor-pointer",
              ])}
              onclick={() => onRowClick?.(row)}
              data-testid="datatable-row"
            >
              {#each visibleColumns as column (column.key)}
                <td
                  class={clsx([
                    "whitespace-nowrap",
                    "px-4",
                    "py-3",
                    "text-sm",
                    "text-neutral-700",
                    column.align === "center" && "text-center",
                    column.align === "right" && "text-right",
                  ])}
                >
                  {row[column.key]}
                </td>
              {/each}
            </tr>
          {/each}
        {/if}
      </tbody>
    </table>
  </div>
</div>

{#if paginated && !loading}
  <div
    class={clsx([
      "mt-4",
      "flex",
      "flex-wrap",
      "items-center",
      "justify-between",
      "gap-4",
    ])}
  >
    <p
      class={clsx(["text-sm", "text-neutral-600"])}
      data-testid="visible-items-text"
    >
      Showing
      <span class="font-medium text-neutral-900">
        {totalRows === 0 ? 0 : (currentPage - 1) * pageSize + 1}
      </span>
      -
      <span class={clsx(["font-medium", "text-gray-900"])}>
        {Math.min(currentPage * pageSize, totalRows)}
      </span>
      of
      <span class="font-medium text-neutral-900">
        {totalRows}
      </span>
    </p>

    <div class="text-xs page-size-container">
      <Select
        id="page-size-select"
        items={pageSizes.map((option) => ({
          value: option.toString(),
          label: option.toString(),
        }))}
        value={pageSize.toString()}
        onchange={(value) => {
          currentPage = 1;
          pageSize = Number.parseInt(value);
        }}
        label={{ text: "Page Size", horizontal: true }}
      />
    </div>

    <nav aria-label="Pagination" class="flex items-center gap-1">
      <Button
        disabled={currentPage === 1}
        ariaLabel="Previous Page"
        handleClick={() => setPage(currentPage - 1)}
        variant="ghost"
        size="xs"
      >
        Previous
      </Button>

      <span
        class="px-2 text-xs text-neutral-600"
        aria-current="page"
        data-testid="current-page"
      >
        Page {currentPage} of {totalPages}
      </span>

      <Button
        disabled={currentPage === totalPages}
        ariaLabel="Next Page"
        variant="ghost"
        size="xs"
        handleClick={() => setPage(currentPage + 1)}
      >
        Next
      </Button>
    </nav>
  </div>
{/if}

<style>
  @reference "../../styles/global.css";

  .page-size-container :global(label) {
    @apply text-xs;
  }
</style>
