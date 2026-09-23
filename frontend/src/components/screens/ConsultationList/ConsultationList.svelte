<script lang="ts">
  import Link from "../../Link.svelte";
  import DataTable from "../../DataTable/DataTable.svelte";
  import Modal from "../../Modal/Modal.svelte";
  import Alert from "../../Alert/Alert.svelte";
  import Title from "../../Title.svelte";
  import LoadingIndicator from "../../LoadingIndicator/LoadingIndicator.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import Warning from "../../svg/material/Warning.svelte";
  import Delete from "../../svg/material/Delete.svelte";
  import Button from "../../inputs/Button/Button.svelte";

  import {
    getConsultationDetailUrl,
    getConsultationEvalUrl,
    getFinaliseThemesUrl,
  } from "../../../global/routes.ts";
  import {
    buildConsultationDeleteQuery,
    buildConsultationsGetQuery,
  } from "../../../global/queries/consultations/queries.ts";
  import type { Consultation } from "../../../global/types.ts";

  interface LinkData {
    url: string;
    ariaLabel: string;
    text: string;
  }

  interface ActionData {
    id: string;
    name: string;
  }

  let deleteConsultationId = $state("");

  const consultations = buildConsultationsGetQuery();
  const consultationDelete = $derived(
    buildConsultationDeleteQuery(deleteConsultationId),
  );

  let consultationsBeingDeleted = $derived(
    consultations.query?.data?.results.filter(
      (consultation: Consultation) =>
        consultation.running_job === "delete-consultation",
    ) || [],
  );

  const consultationRows = $derived(
    consultations.query.data?.results.map((consultation: Consultation) => ({
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
      actions: {
        id: consultation.id,
        name: consultation.title,
      },
    })),
  );
</script>

<section>
  <Title level={2} text="Consultations" />
  <p class="text-neutral-500 text-sm">
    {#if consultations.query.isPending}
      Loading consultations...
    {:else}
      {consultations.query?.data?.results.length || 0} consultations
    {/if}
  </p>
</section>

{#if consultationsBeingDeleted.length > 0}
  <div class="mt-4 blink-light">
    <Alert variant="info">
      {consultationsBeingDeleted.length} consultation{consultationsBeingDeleted.length >
      1
        ? "s are"
        : " is"} currently being deleted. This may take a while.
    </Alert>
  </div>
{/if}

<section class="mt-4">
  <DataTable
    columns={[
      { label: "Name", key: "name", sortable: true },
      {
        label: "Date Created",
        key: "createdAt",
        sortable: true,
        sortValue: (item) =>
          new Date((item as { createdAt: string }).createdAt).getTime(),
        displayValue: (item) =>
          new Date(
            (item as { createdAt: string }).createdAt,
          ).toLocaleDateString(),
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
      },
      {
        label: "Actions",
        key: "actions",
        sortable: false,
      },
    ]}
    rows={consultationRows}
    loadingCondition={consultations.query.isPending}
    errorCondition={Boolean(consultations.query.error)}
    loadingText="Loading consultations..."
    emptyText="No consultations available"
    errorText={consultations.query.error?.message || "There has been an error"}
    columnSelect={false}
  >
    {#snippet cellContent(content, row, column)}
      {#if ["evalLink", "themesLink", "dashboardLink"].includes(column.key)}
        {@const linkData = row[column.key] as LinkData}

        <Link href={linkData.url} ariaLabel={linkData.ariaLabel}>
          {linkData.text}
        </Link>
      {:else if column.key === "actions"}
        {@const { id, name } = content as ActionData}
        {@const deleting = consultationsBeingDeleted.find(
          (consultation: Consultation) => consultation.id === id,
        )}

        <div>
          <Button
            ariaLabel={`Delete ${name}`}
            handleClick={() => {
              deleteConsultationId = id;
            }}
            disabled={deleting}
          >
            {#if deleting}
              <LoadingIndicator size="1rem" />
            {:else}
              <MaterialIcon color="fill-neutral-500">
                <Delete />
              </MaterialIcon>
            {/if}

            {deleting ? "Deleting..." : "Delete"}
          </Button>
        </div>
      {:else}
        <span>{content}</span>
      {/if}
    {/snippet}
  </DataTable>
</section>

<Modal
  variant="warning"
  open={Boolean(deleteConsultationId)}
  setOpen={(newOpen: boolean) => {
    if (newOpen === false) {
      deleteConsultationId = "";
    }
  }}
  title="Delete consultation"
  Icon={Warning}
  canCancel={true}
  confirmText="Delete"
  handleConfirm={async () => {
    await consultationDelete.fetch({});

    deleteConsultationId = "";

    // Refresh consultations as running_job should now be stale
    consultations.fetch();
  }}
>
  <p>
    Are you sure you would like to <strong>delete</strong> consultation "{consultations.query.data?.results.find(
      (consultation: Consultation) => consultation.id === deleteConsultationId,
    )?.title}"? This action is <strong>irreversible</strong>.
  </p>
</Modal>
