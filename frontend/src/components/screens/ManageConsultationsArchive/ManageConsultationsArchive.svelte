<script lang="ts" module>
  export const buildDateTimeString = (date: Date) => {
    const dateString = date.toLocaleString(navigator.language, {
      month: "long",
      day: "2-digit",
      year: "numeric",
    });
    const timeString = date.toLocaleTimeString(navigator.language, {
      hour: "2-digit",
      minute: "2-digit",
    });

    return `${dateString} at ${timeString}`;
  };
</script>

<script lang="ts">
  import { getSupportConsultationDetails } from "../../../global/routes";

  import Link from "../../Link.svelte";
  import Title from "../../Title.svelte";
  import DataTable from "../../DataTable/DataTable.svelte";

  interface LinkData {
    url: string;
    text: string;
    ariaLabel: string;
  }

  interface Consultation {
    id: string;
    title: string;
    created_at: string;
  }

  interface DisplayConsultation {
    createdAt: string;
    name: LinkData;
  }

  interface Props {
    consultations: Consultation[];
  }

  let { consultations = [] }: Props = $props();

  let displayConsultations = $derived(
    consultations.map((consultation) => ({
      name: {
        url: getSupportConsultationDetails(consultation.id),
        text: consultation.title,
        ariaLabel: `View ${consultation.title}`,
      },
      createdAt: consultation.created_at,
    })),
  );

  const getFormattedDateTime = (item: DisplayConsultation) => {
    const dateObj = new Date(item.createdAt);
    return buildDateTimeString(dateObj);
  };
</script>

<Title level={1} text="Consultations" />

<DataTable
  columns={[
    {
      key: "name",
      label: "Name",
      sortable: true,
      sortValue: (item) => item.name.text,
      filterValue: (item) => item.name.text,
    },
    {
      key: "createdAt",
      label: "Date Created",
      sortable: true,
      sortValue: (item) => new Date(item.createdAt).getTime(),
      displayValue: (item) => getFormattedDateTime(item),
      filterValue: (item) => getFormattedDateTime(item),
    },
  ]}
  rows={displayConsultations}
  emptyText="No consultations found for the given query"
  initialSort={{
    key: "createdAt",
    direction: "desc",
  }}
  searchPlaceholder="Search consultations"
>
  {#snippet cellContent(content, row, column)}
    {#if column.key === "name"}
      {@const linkData = row[column.key] as LinkData}

      <Link href={linkData.url} ariaLabel={linkData.ariaLabel}>
        {linkData.text}
      </Link>
    {:else}
      <span>{content}</span>
    {/if}
  {/snippet}
</DataTable>
