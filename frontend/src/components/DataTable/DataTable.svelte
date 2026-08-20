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

  type Props = {
    rows?: T[];
    columns: DataTableColumn<T>[];
    caption?: string;
    loading?: boolean;
    sortable?: boolean;
    initialSort?: SortState<T>;
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
    onSortChange,
    onRowClick,
  }: Props = $props();

  let sort = $derived<SortState<T> | null>(initialSort ?? null);

  let announcement = $state("");

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
            >
              {#if sortable && column.sortable !== false}
                <button
                  type="button"
                  class={clsx([
                    "inline-flex",
                    "min-h-8",
                    "w-full",
                    "items-center",
                    "justify-start",
                    "gap-2",
                    "rounded-md",
                    "text-left",
                    "cursor-pointer",
                    "hover:bg-neutral-100",
                    "focus:outline-none",
                    "focus-visible:ring-2",
                    "focus-visible:ring-blue-500",
                    "focus-visible:ring-offset-2",
                  ])}
                  aria-label={getSortAriaLabel(column)}
                  onclick={() => sortBy(column)}
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
                </button>
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
        {:else if sortedRows.length === 0}
          {@render messageRow(noDataMessage)}
        {:else}
          {#each sortedRows as row, i (i)}
            <tr
              class={clsx([
                "transition-colors",
                "hover:bg-neutral-50",
                Boolean(onRowClick) && "cursor-pointer",
              ])}
              onclick={() => onRowClick?.(row)}
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
