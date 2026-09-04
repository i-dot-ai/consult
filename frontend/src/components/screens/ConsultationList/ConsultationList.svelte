<script lang="ts">
  import Link from "../../Link.svelte";
  import DataTable from "../../DataTable/DataTable.svelte";

  import {
    getConsultationDetailUrl,
    getConsultationEvalUrl,
    getFinaliseThemesUrl,
  } from "../../../global/routes.ts";
  import { buildConsultationsGetQuery } from "../../../global/queries/consultations/queries.ts";
  import type { Consultation } from "../../../global/types.ts";

  const consultations = buildConsultationsGetQuery();
  const consultationRows = $derived(consultations.query.data?.results.map((consultation: Consultation) => ({
    name: consultation.title,
    createdAt: consultation.created_at,
    evalLink: {
      url: getConsultationEvalUrl(consultation.id),
      ariaLabel: `View Evaluation for ${consultation.title}`,
      text: "View Evaluation",
    },
    themesLink: {
      url: getFinaliseThemesUrl(consultation.id),
      ariaLabel: `Finalise Themes for ${consultation.title}`,
      text: "Finalise Themes",
    },
    dashboardLink: {
      url: getConsultationDetailUrl(consultation.id),
      ariaLabel: `View Dashboard for ${consultation.title}`,
      text: "View Dashboard",
    },
  })))
</script>

<section class="mt-4">
  <DataTable
    columns={[
      { label: "Name", key: "name", sortable: true },
      {
        label: "Date Created",
        key: "createdAt",
        sortable: true,
        sortValue: (item: any) => new Date(item.createdAt).getTime(),
        displayValue: (item: any) => new Date(item.createdAt).toLocaleDateString(),
      },
      {
        label: "Evaluation",
        key: "evalLink",
        sortable: false,
      },
      {
        label: "Themes",
        key: "themesLink",
        sortable: false,
      },
      {
        label: "Dashboard",
        key: "dashboardLink",
        sortable: false,
      }
    ]}
    rows={consultationRows}
    loadingCondition={consultations.query.isPending}
    errorCondition={Boolean(consultations.query.error)}
    loadingText="Loading consultations..."
    emptyText={"No consultations available"}
    errorText={consultations.query.error?.message || "There has been an error"}
  >
    {#snippet cellContent(content, row, column)}
      {#if ["evalLink", "themesLink", "dashboardLink"].includes(column.key)}
        {@const rowData = row[column.key]}

        <Link
          href={rowData.url}
          ariaLabel={rowData.ariaLabel}
        >
          {rowData.text}
        </Link>
      {:else}
        <span>{content}</span>
      {/if}
    {/snippet}
  </DataTable>
</section>
