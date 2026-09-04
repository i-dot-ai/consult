<script lang="ts">
  import { slide } from "svelte/transition";

  import Title from "../../Title.svelte";
  import Link from "../../Link.svelte";
  import Alert from "../../Alert.svelte";
  import DataTable from "../../DataTable/DataTable.svelte";
  import LoadingMessage from "../../LoadingMessage/LoadingMessage.svelte";

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
  {#if consultations.query.error}
    <Alert>
      <p>{consultations.query.error?.message || "An error happened"}</p>
    </Alert>
  {:else if consultations.query.isPending}
    <p transition:slide>
      <LoadingMessage message="Loading consultations..." />
    </p>
  {:else if consultations.query?.data?.results?.length === 0}
    No consultations available
  {:else}
    <ul>
      {#each consultations.query.data?.results as consultation (consultation.id)}
        <li>
          <Title level={2} text={consultation.title} />

          <div class="flex flex-wrap gap-4">
            <Link
              href={getConsultationEvalUrl(consultation.id)}
              ariaLabel={`View Evaluation for ${consultation.title}`}
            >
              View Evaluation
            </Link>
            <Link
              href={getFinaliseThemesUrl(consultation.id)}
              ariaLabel={`Finalise Themes for ${consultation.title}`}
            >
              Finalise Themes
            </Link>
            <Link
              href={getConsultationDetailUrl(consultation.id)}
              ariaLabel={`View Dashboard for ${consultation.title}`}
            >
              View Dashboard
            </Link>
          </div>
        </li>
      {/each}
    </ul>
  {/if}

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
    loading={consultations.query.isPending}
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
