<script lang="ts">
  import clsx from "clsx";

  import { fade } from "svelte/transition";

  import { getSupportConsultationDetails } from "../../../global/routes";
  import { formatDate } from "../../../global/utils";

  import Link from "../../Link.svelte";
  import Title from "../../Title.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import ArrowForward from "../../svg/material/ArrowForward.svelte";
  import Button from "../../inputs/Button/Button.svelte";
  import TextInput from "../../inputs/TextInput/TextInput.svelte";

  interface Consultation {
    id: string;
    title: string;
    created_at: string;
  }
  interface Props {
    consultations: Consultation[];
  }

  let { consultations = [] }: Props = $props();

  const SORT_DIRECTION = {
    ASC: "asc",
    DESC: "desc",
    NONE: "none",
  } as const;

  type SortDirection =
    | typeof SORT_DIRECTION.ASC
    | typeof SORT_DIRECTION.DESC
    | typeof SORT_DIRECTION.NONE;

  let nameSortDirection = $state<SortDirection>(SORT_DIRECTION.NONE);
  let dateSortDirection = $state<SortDirection>(SORT_DIRECTION.DESC);
  let searchValue = $state("");

  let displayConsultations = $derived.by(() => {
    let result = [...consultations];

    if (dateSortDirection !== SORT_DIRECTION.NONE) {
      result.sort((a, b) => {
        const dateA = new Date(a.created_at).getTime();
        const dateB = new Date(b.created_at).getTime();

        if (dateA === dateB) {
          return 0;
        }

        const dateDirectionMultiplier =
          dateSortDirection === SORT_DIRECTION.ASC ? -1 : 1;
        return dateA + dateB * dateDirectionMultiplier;
      });
    }

    if (nameSortDirection !== SORT_DIRECTION.NONE) {
      result.sort((a, b) => {
        const nameA = a.title;
        const nameB = b.title;

        const nameDirectionMultiplier =
          nameSortDirection === SORT_DIRECTION.ASC ? 1 : -1;

        if (nameA > nameB) {
          return -1 * nameDirectionMultiplier;
        } else if (nameA < nameB) {
          return 1 * nameDirectionMultiplier;
        }
        return 0;
      });
    }

    if (searchValue) {
      result = result.filter(consultation => {
        const textA = consultation.title.toLocaleLowerCase();
        const textB = searchValue.toLocaleLowerCase();
        return textA.includes(textB);
      })
    }

    return result;
  });
</script>

{#snippet sortButton(
  text: string,
  direction: SortDirection,
  setDirection: (newDirection: SortDirection) => void,
)}
  <Button
    variant="ghost"
    handleClick={() => {
      if (direction === SORT_DIRECTION.NONE) {
        setDirection(SORT_DIRECTION.DESC);
      } else if (direction === SORT_DIRECTION.DESC) {
        setDirection(SORT_DIRECTION.ASC);
      } else {
        setDirection(SORT_DIRECTION.NONE);
      }
    }}
    ariaLabel={`sort consultations by ${text}`}
    ariaControls="consultations-list"
  >
    {text}
    {#if direction !== SORT_DIRECTION.NONE}
      <div
        class={clsx([
          "transition-transform",
          direction === SORT_DIRECTION.ASC ? "rotate-90" : "-rotate-90",
        ])}
      >
        <MaterialIcon color="fill-neutral-500">
          <ArrowForward />
        </MaterialIcon>
      </div>
    {/if}
  </Button>
{/snippet}

<Title level={1} text="Consultations" />

<div class="mt-2 w-full md:w-1/3">
  <TextInput
    id={"search-consultations"}
    label="Search consultations"
    placeholder={"Find consultation..."}
    hideLabel={true}
    value={searchValue}
    setValue={(newValue) => searchValue = newValue.trim()}
  />
</div>

<div class="overflow-x-auto">
  <table class="w-full whitespace-nowrap text-left">
    <thead class="font-bold">
      <tr>
        <th class="py-2 pr-2">
          {@render sortButton(
            "Name",
            nameSortDirection,
            (newSortDirection: SortDirection) => {
              nameSortDirection = newSortDirection;
            },
          )}
        </th>
        <th class="py-2 pr-2">
          {@render sortButton(
            "Created At",
            dateSortDirection,
            (newSortDirection: SortDirection) => {
              dateSortDirection = newSortDirection;
            },
          )}
        </th>
      </tr>
    </thead>
    <tbody id="consultations-list">
      {#if displayConsultations.length === 0}
        <tr in:fade={{ duration: 200 }} class="border-t hover:bg-gray-50">
          <td colspan="2" class="text-neutral-500">
            No consultation found for the given query
          </td>
        </tr>
      {/if}

      {#each displayConsultations as consultation, i (i)}
        <tr transition:fade={{ duration: 200 }} class="border-t hover:bg-gray-50" data-testid="consultation-item">
          <td data-testid="title" class="py-2 pr-2">
            <Link href={getSupportConsultationDetails(consultation.id)}>
              {consultation.title}
            </Link>
          </td>
          <td data-testid="created-at" class="py-2 pr-2">{formatDate(consultation.created_at)}</td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>
