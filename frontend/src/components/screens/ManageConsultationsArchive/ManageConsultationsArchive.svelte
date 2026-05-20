<script lang="ts">
  import clsx from "clsx";

  import { getSupportConsultationDetails } from "../../../global/routes";
  import { formatDate } from "../../../global/utils";

  import Button from "../../inputs/Button/Button.svelte";
  import Link from "../../Link.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import ArrowForward from "../../svg/material/ArrowForward.svelte";
  import Title from "../../Title.svelte";

  interface Consultation {
    id: string;
    title: string;
    created_at: string;
  }
  interface Props {
    consultations: Consultation[];
  }

  let {
    consultations = [],
  }: Props = $props();

  const SORT_DIRECTION = {
    ASC: "asc",
    DESC: "desc",
  } as const;

  let sortDirection = $state<typeof SORT_DIRECTION.ASC | typeof SORT_DIRECTION.DESC>(SORT_DIRECTION.DESC);

  let displayConsultations = $derived(consultations.toSorted((a, b) => {
    const dateA = new Date(a.created_at);
    const dateB = new Date(b.created_at);

    const directionMultiplier = sortDirection === SORT_DIRECTION.ASC ? -1 : 1;
    return dateA.getTime() + (dateB.getTime() * directionMultiplier);
  }));
</script>

<Title level={1} text="Consultations" />
<div class="overflow-x-auto">
  <table class="w-full whitespace-nowrap text-left">
    <thead class="font-bold">
      <tr>
        <th class="py-2 pr-2">name</th>
        <th class="py-2 pr-2">
          <Button
            variant="ghost"
            handleClick={() => {
              sortDirection = sortDirection === SORT_DIRECTION.ASC ? "desc" : "asc";
            }}
            ariaLabel="sort consultations by date"
            ariaControls="consultations-list"
          >
            created at
            <div class={clsx([
              "transition-transform",
              sortDirection === SORT_DIRECTION.ASC
                ? "rotate-90"
                : "-rotate-90"
            ])}>
              <MaterialIcon color="fill-neutral-500">
                <ArrowForward />
              </MaterialIcon>
            </div>
          </Button>
        </th>
      </tr>
    </thead>
    <tbody id="consultations-list">
      {#each displayConsultations as consultation, i (i)}
        <tr class="border-t hover:bg-gray-50">
          <td class="py-2 pr-2">
            <Link href={getSupportConsultationDetails(consultation.id)}>
              {consultation.title}
            </Link>
          </td>
          <td class="py-2 pr-2">{formatDate(consultation.created_at)}</td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>