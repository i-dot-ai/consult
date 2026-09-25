<script lang="ts">
  import { onDestroy } from "svelte";
  import { fade } from "svelte/transition";

  import Link from "../../Link.svelte";
  import DataTable from "../../DataTable/DataTable.svelte";
  import Modal from "../../Modal/Modal.svelte";
  import Alert from "../../Alert/Alert.svelte";
  import Title from "../../Title.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import Warning from "../../svg/material/Warning.svelte";
  import Delete from "../../svg/material/Delete.svelte";
  import Button from "../../inputs/Button/Button.svelte";
  import { type CurrentUserGetResponse } from "../../../global/queries/users/types.ts";

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
  import Panel from "../../dashboard/Panel/Panel.svelte";
  import { buildCurrentUserGetQuery } from "../../../global/queries/users/queries.ts";

  interface LinkData {
    url: string;
    ariaLabel: string;
    text: string;
  }

  interface NameCellData {
    text: string;
    links: LinkData[];
  }

  interface ActionData {
    id: string;
    name: string;
    createdBy: string;
  }

  interface Props {
    deleteAlertDuration?: number;
  }

  const { deleteAlertDuration = 5000 }: Props = $props();

  let deleteConsultationId = $state("");
  let alerts: string[] = $state([]);

  const user = buildCurrentUserGetQuery();
  const consultations = buildConsultationsGetQuery();
  const consultationDelete = $derived(
    buildConsultationDeleteQuery(deleteConsultationId),
  );

  const consultationsToDisplay = $derived(
    consultations.query.data?.results.filter(
      (consultation: Consultation) =>
        consultation.running_job !== "delete-consultation",
    ) || [],
  );

  const consultationRows = $derived(
    consultationsToDisplay.map((consultation: Consultation) => ({
      name: {
        text: consultation.title,
        links: [
          {
            url: getConsultationEvalUrl(consultation.id),
            ariaLabel: `View Evaluation for ${consultation.title}`,
            text: "View Evaluation",
          },
          {
            url: getFinaliseThemesUrl(consultation.id),
            ariaLabel: `Finalise Themes for ${consultation.title}`,
            text: "Finalise Themes",
          },
          {
            url: getConsultationDetailUrl(consultation.id),
            ariaLabel: `View Dashboard for ${consultation.title}`,
            text: "View Dashboard",
          },
        ],
      },
      createdAt: consultation.created_at,
      createdBy: consultation.created_by,
      actions: {
        id: consultation.id,
        name: consultation.title,
        createdBy: consultation.created_by,
      },
    })),
  );

  function canDelete(
    userData: CurrentUserGetResponse,
    consultationCreatedBy: string,
  ) {
    const isUserStaff = userData?.is_staff;
    const isUserCreator = userData?.email === consultationCreatedBy;

    return isUserStaff || isUserCreator;
  }

  let alertTimeouts: ReturnType<typeof setTimeout>[] = [];

  onDestroy(() => {
    alertTimeouts.forEach((timeout) => {
      clearInterval(timeout);
    });
  });
</script>

{#snippet nullCell()}
  <hr class="my-2 w-12" />
{/snippet}

<section>
  <Title level={2} text="Consultations" />
  <p class="text-neutral-500 text-sm">
    {#if consultations.query.isPending}
      Loading consultations...
    {:else}
      {consultationsToDisplay.length || 0} consultations
    {/if}
  </p>
</section>

<section>
  {#if alerts.length === 0}
    <div class="sr-only">No alerts to list</div>
  {/if}

  {#each alerts as alert, i (i)}
    <div class="mt-4" transition:fade>
      <Alert variant="info">
        {alert}
      </Alert>
    </div>
  {/each}
</section>

<section class="mt-4">
  <DataTable
    columns={[
      {
        label: "Name",
        key: "name",
        sortable: true,
        sortValue: (details) => (details.name as NameCellData).text,
        filterValue: (details) => (details.name as NameCellData).text,
      },
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
        filterValue: (item) =>
          new Date(
            (item as { createdAt: string }).createdAt,
          ).toLocaleDateString(),
      },
      {
        label: "Created by",
        key: "createdBy",
        sortable: true,
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
      {#if column.key === "name"}
        {@const cellData = row[column.key] as NameCellData}

        <div>
          <p>{cellData.text}</p>

          <div class="flex gap-3 mt-2">
            {#each cellData.links as link, i (i)}
              <Link href={link.url} ariaLabel={link.ariaLabel}>
                {link.text}
              </Link>
            {/each}
          </div>
        </div>
      {:else if column.key === "createdBy"}
        {@const userData = user.query?.data as CurrentUserGetResponse}

        {#if !content}
          {@render nullCell()}
        {:else if content === userData.email}
          <span>You</span>
        {:else}
          <span class="text-neutral-500">{content}</span>
        {/if}
      {:else if column.key === "actions"}
        {@const { id, name, createdBy } = content as ActionData}
        {@const userData = user.query?.data as CurrentUserGetResponse}

        {#if canDelete(userData, createdBy)}
          <div>
            <Button
              ariaLabel={`Delete ${name}`}
              handleClick={() => {
                deleteConsultationId = id;
              }}
            >
              <MaterialIcon color="fill-neutral-500">
                <Delete />
              </MaterialIcon>

              Delete
            </Button>
          </div>
        {:else}
          {@render nullCell()}
        {/if}
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
  title="Delete consultation?"
  Icon={Warning}
  canCancel={true}
  confirmText="Delete consultation"
  handleConfirm={async () => {
    // Trigger deletion on the server
    await consultationDelete.fetch({});

    // Display alert that the consultation has been deleted
    const consultationToDelete = consultationsToDisplay.find(
      (consultation: Consultation) => consultation.id === deleteConsultationId,
    );
    const newAlertText = `Consultation ${consultationToDelete?.title ?? deleteConsultationId} has been deleted.`;
    alerts = [...alerts, newAlertText];

    // Set timeout to remove alert
    const newAlertTimeout = setTimeout(() => {
      alerts = alerts.filter((alert) => alert !== newAlertText);
    }, deleteAlertDuration);

    alertTimeouts = [...alertTimeouts, newAlertTimeout];

    // Reset consultation selected for deletion
    deleteConsultationId = "";

    // Refresh consultations as running_job should now be stale
    consultations.fetch();
  }}
>
  <p>
    This deletes {consultations.query.data?.results.find(
      (consultation: Consultation) => consultation.id === deleteConsultationId,
    )?.title} and all its responses, themes and records. It cannot be undone.

    <Panel variant="default">
      Large consultations can take a while to delete. You can leave this page
      while it happens.
    </Panel>
  </p>
</Modal>
