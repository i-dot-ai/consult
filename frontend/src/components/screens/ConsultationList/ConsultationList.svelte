<script lang="ts">
  import clsx from "clsx";

  import { fade } from "svelte/transition";

  import Link from "../../Link.svelte";
  import DataTable from "../../DataTable/DataTable.svelte";
  import Modal from "../../Modal/Modal.svelte";
  import Alert from "../../Alert/Alert.svelte";
  import Title from "../../Title.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import Warning from "../../svg/material/Warning.svelte";
  import Delete from "../../svg/material/Delete.svelte";
  import Close from "../../svg/material/Close.svelte";
  import Button from "../../inputs/Button/Button.svelte";

  import {
    getConsultationDetailUrl,
    getConsultationEvalUrl,
    getFinaliseThemesUrl,
    getSupportUserDetail,
  } from "../../../global/routes.ts";
  import {
    buildConsultationDeleteQuery,
    buildConsultationsGetQuery,
  } from "../../../global/queries/consultations/queries.ts";
  import type { Consultation } from "../../../global/types.ts";
  import Panel from "../../dashboard/Panel/Panel.svelte";
  import { buildCurrentUserGetQuery } from "../../../global/queries/users/queries.ts";
  import { type CurrentUserGetResponse } from "../../../global/queries/users/types.ts";

  interface AlertData {
    text: string;
    variant: "success" | "error";
  }

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
    enableV2?: boolean;
  }

  const { deleteAlertDuration = 5000, enableV2 = true }: Props = $props();

  let deleteConsultationId = $state("");
  let alerts: AlertData[] = $state([]);

  const user = $derived(enableV2 ? buildCurrentUserGetQuery() : null);
  const consultations = buildConsultationsGetQuery();
  const consultationDelete = $derived(
    buildConsultationDeleteQuery(deleteConsultationId),
  );

  const consultationsToDisplay: Consultation[] = $derived(
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
      createdBy:
        typeof consultation.created_by === "string"
          ? consultation.created_by // v1 will return only email as string
          : consultation.created_by?.email, // v2 will return entire User obj
      ...(enableV2
        ? {
            team: consultation.users,
            status: consultation.stage,
            actions: {
              id: consultation.id,
              name: consultation.title,
              createdBy: consultation.created_by,
            },
          }
        : {}),
    })),
  );

  function getUserColor(id: number) {
    const SCALE_AMOUNT = 10000;
    const CLASSES = [
      "bg-neutral-500",
      "bg-neutral-300",
      "bg-neutral-400",
      "bg-neutral-700",
    ];

    const number = Number(id);
    const sineValue = Math.sin(number);
    const scaledValue = sineValue * SCALE_AMOUNT;

    const integerPart = Math.floor(scaledValue);
    const fractionalPart = scaledValue - integerPart;

    const bucket = Math.floor(fractionalPart * CLASSES.length);
    return CLASSES[bucket];
  }

  function canDelete(
    userData: CurrentUserGetResponse | undefined,
    consultationCreatedBy: string,
  ) {
    const isUserStaff = userData?.is_staff;
    const isUserCreator = userData?.email === consultationCreatedBy;

    return isUserStaff || isUserCreator;
  }

  function removeAlert(alertToRemove: AlertData) {
    alerts = alerts.filter((alert) => alert.text !== alertToRemove.text);
  }

  function addAlert(newAlert: AlertData) {
    alerts = [...alerts, newAlert];
  }
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

  {#each alerts as alert, i (alert.text + i)}
    <div class="mt-4" transition:fade>
      <Alert
        variant={alert.variant}
        onTimeout={() => {
          removeAlert(alert);
        }}
        timeoutDelay={deleteAlertDuration}
      >
        <div class="flex justify-between items-center gap-2">
          <span>
            {alert.text}
          </span>

          <Button variant="ghost" handleClick={() => removeAlert(alert)}>
            <MaterialIcon color="fill-neutral-500">
              <Close />
            </MaterialIcon>
          </Button>
        </div>
      </Alert>
    </div>
  {/each}
</section>

{#if consultationsToDisplay.length === 0 && !consultations.query.isPending}
  <Panel variant="default">
    <div class="my-12">
      <p class="text-lg text-center mb-2">You have no consultations yet</p>
      <p class="text-sm text-neutral-500 text-center">
        Add a consultation, then upload the responses.
      </p>
      <!-- TODO: Add create consultation button -->
    </div>
  </Panel>
{:else}
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
        ...(enableV2
          ? ([
              {
                label: "Team",
                key: "team",
                sortable: false,
              },
              {
                label: "Status",
                key: "status",
                sortable: true,
              },
              {
                label: "Actions",
                key: "actions",
                sortable: false,
              },
            ] as const)
          : []),
      ]}
      rows={consultationRows}
      loadingCondition={consultations.query.isPending}
      errorCondition={Boolean(consultations.query.error)}
      loadingText="Loading consultations..."
      emptyText="No consultations available"
      errorText={consultations.query.error?.message ||
        "There has been an error"}
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
          {@const userData = user?.query?.data as CurrentUserGetResponse}

          {#if !content}
            {@render nullCell()}
          {:else if content === userData?.email}
            <span>You</span>
          {:else}
            <span class="text-neutral-500">{content}</span>
          {/if}
        {:else if column.key === "team"}
          {@const users = content as Consultation["users"]}
          {@const currentUser = user?.query?.data}

          {#if !content || users?.length === 0}
            {@render nullCell()}
          {:else}
            <div class="flex gap-2 items-center">
              {#each users as teamMember (teamMember.id)}
                <svelte:element
                  this={currentUser?.is_staff ? "a" : "div"}
                  href={currentUser?.is_staff
                    ? getSupportUserDetail(teamMember.id.toString())
                    : undefined}
                  aria-label={currentUser?.is_staff
                    ? `View details for ${teamMember.email}`
                    : undefined}
                  title={teamMember.email}
                >
                  <div
                    class={clsx([
                      "flex",
                      "justify-center",
                      "items-center",
                      "w-6",
                      "h-6",
                      "p-1",
                      "text-white",
                      "text-xs",
                      "rounded-full",
                      "transition-colors",
                      "hover:bg-primary",
                      getUserColor(teamMember.id),
                    ])}
                  >
                    {teamMember.email.charAt(0).toUpperCase()}
                  </div>
                </svelte:element>
              {/each}
            </div>
          {/if}
        {:else if column.key === "status"}
          {@const status = content as Consultation["stage"]}
          {@const DISPLAY_TEXTS = {
            setup: "Setting up data",
            finding_themes: "Finding themes",
            finalising_themes: "Finalising themes",
            assigning_themes: "Assigning themes",
            analysis: "Analysis",
          } as const}

          <span>
            {DISPLAY_TEXTS[status] || "Invalid status"}
          </span>
        {:else if column.key === "actions"}
          {@const { id, name, createdBy } = content as ActionData}
          {@const userData = user?.query?.data as CurrentUserGetResponse}

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
    title="Delete consultation"
    Icon={Warning}
    canCancel={true}
    confirmText="Delete consultation"
    handleConfirm={async () => {
      // Prepare alert
      let newAlertText: AlertData["text"];
      let newAlertVariant: AlertData["variant"];

      const consultationToDelete = consultationsToDisplay.find(
        (consultation: Consultation) =>
          consultation.id === deleteConsultationId,
      );
      const consultationTitle = `${consultationToDelete?.title ?? deleteConsultationId}`;
      newAlertText = `Consultation ${consultationTitle} has been deleted.`;
      newAlertVariant = "success";

      // Trigger deletion on the server
      try {
        await consultationDelete.fetch({});
      } catch {
        console.error(consultationDelete.query?.error?.message);
        newAlertText = `Consultation ${consultationTitle} could not be deleted.`;
        newAlertVariant = "error";
      }

      // Display alert
      addAlert({
        text: newAlertText,
        variant: newAlertVariant,
      });

      // Reset consultation selected for deletion
      deleteConsultationId = "";

      // Refresh consultations as running_job should now be stale
      consultations.fetch();
    }}
  >
    <p>
      Deleting removes the responses, the themes and the analysis. This cannot
      be undone.

      <Panel variant="default">
        {consultations.query.data?.results.find(
          (consultation: Consultation) =>
            consultation.id === deleteConsultationId,
        )?.title}
      </Panel>
    </p>
  </Modal>
{/if}
