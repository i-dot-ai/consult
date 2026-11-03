<script lang="ts">
  import { tick } from "svelte";

  import Alert from "../../Alert/Alert.svelte";
  import DataTable, {
    type DataTableColumn,
  } from "../../DataTable/DataTable.svelte";
  import Button from "../../inputs/Button/Button.svelte";
  import Link from "../../Link.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import SkeletonText from "../../SkeletonText/SkeletonText.svelte";
  import Tag from "../../Tag/Tag.svelte";
  import Title from "../../Title.svelte";
  import Check from "../../svg/material/Check.svelte";
  import Close from "../../svg/material/Close.svelte";
  import ErrorIcon from "../../svg/material/Error.svelte";
  import AddPeopleModal from "./AddPeopleModal.svelte";
  import RemovePersonModal from "./RemovePersonModal.svelte";
  import {
    getAddedNotice,
    orderPeople,
    getPeopleCountText,
    type AddResult,
  } from "./people";

  import {
    buildConsultationV2AssignUsersQuery,
    buildConsultationV2GetQuery,
    buildConsultationV2RemoveUserQuery,
  } from "../../../global/queries/consultations/queries";
  import type {
    ConsultationV2AssignUsersResponse,
    ConsultationV2User,
  } from "../../../global/queries/consultations/types";
  import { buildCurrentUserGetQuery } from "../../../global/queries/users/queries";

  interface Props {
    consultationId: string;
    backHref: string;
    backText: string;
  }

  type PersonRow = { email: string; user: ConsultationV2User };

  let { consultationId, backHref, backText }: Props = $props();

  const PAGE_SIZE = 10;

  const consultation = $derived(buildConsultationV2GetQuery(consultationId));
  const user = buildCurrentUserGetQuery();
  const assignUsers = $derived(
    buildConsultationV2AssignUsersQuery(consultationId),
  );
  const removeUser = $derived(
    buildConsultationV2RemoveUserQuery(consultationId),
  );

  let consultationData = $derived(consultation.query.data);
  let userData = $derived(user.query.data);
  let loading = $derived(consultation.query.isPending || user.query.isPending);
  let failedToLoad = $derived(consultation.query.isError || user.query.isError);
  let canManage = $derived(
    Boolean(consultationData?.is_owner || userData?.is_staff),
  );
  let people = $derived(consultationData ? orderPeople(consultationData) : []);
  let creatorId = $derived(consultationData?.created_by?.id);
  let rows: PersonRow[] = $derived(
    people.map((person) => ({ email: person.email, user: person })),
  );
  let columns: DataTableColumn<PersonRow>[] = $derived(
    canManage
      ? [
          { key: "email", label: "Email address" },
          { key: "user", label: "Actions", align: "right" },
        ]
      : [{ key: "email", label: "Email address" }],
  );
  let countText = $derived(getPeopleCountText(people.length));
  let adding = $state(false);
  let personToRemove = $state<ConsultationV2User | null>(null);
  let notice = $state("");
  let dialogOpener: HTMLElement | null = null;
  let noticeEl = $state<HTMLElement | null>(null);
  let failure = $state("");

  function openAddPeople() {
    dialogOpener = document.activeElement as HTMLElement | null;
    adding = true;
  }

  function openRemove(person: ConsultationV2User) {
    dialogOpener = document.activeElement as HTMLElement | null;
    personToRemove = person;
  }

  // A cancelled dialog hands focus back to the control that opened it.
  async function closeDialogs() {
    adding = false;
    personToRemove = null;
    await tick();
    dialogOpener?.focus();
  }

  async function showNotice(text: string) {
    notice = text;
    await tick();
    noticeEl?.focus();
  }

  async function addPeople(
    newEmails: string[],
    alreadyOnEmails: string[],
  ): Promise<AddResult> {
    if (newEmails.length === 0) {
      adding = false;
      await showNotice(getAddedNotice(0, alreadyOnEmails));
      return { outcome: "added" };
    }
    try {
      const data = (await assignUsers.fetch({
        body: { emails: newEmails },
      })) as ConsultationV2AssignUsersResponse;
      adding = false;
      await consultation.fetch();
      await showNotice(getAddedNotice(data.added_count, alreadyOnEmails));
      return { outcome: "added" };
    } catch (error) {
      console.error(error);
      return { outcome: "failed" };
    }
  }

  async function removePerson(person: ConsultationV2User) {
    try {
      await removeUser.fetch({ params: { userId: String(person.id) } });
      personToRemove = null;
      await consultation.fetch();
      await showNotice(`${person.email} removed.`);
    } catch (error) {
      console.error(error);
      await closeDialogs();
      failure = `${person.email} was not removed. Try again.`;
    }
  }
</script>

<div class="mt-8 mb-4">
  <Link href={backHref} ariaLabel={backText} role="link">{backText}</Link>
</div>

<div class="flex flex-wrap items-start justify-between gap-4">
  <Title level={2}>People on this consultation</Title>
  {#if canManage}
    <Button variant="primary" size="sm" handleClick={openAddPeople}>
      Add people
    </Button>
  {/if}
</div>

<p class="mt-2 text-sm text-neutral-500">
  {#if loading}
    <SkeletonText length={4} />
  {:else if consultationData}
    {consultationData.title} · {countText}
  {/if}
</p>

{#if !loading && !failedToLoad && !canManage}
  <p class="mt-2 text-sm text-neutral-500">
    The person who created this consultation adds and removes people.
  </p>
{/if}

{#if notice}
  <div class="mt-4" role="status" tabindex="-1" bind:this={noticeEl}>
    <Alert variant="success" Icon={Check}>
      <div class="flex items-center justify-between gap-2">
        <span>{notice}</span>
        <Button
          variant="ghost"
          ariaLabel="Dismiss this message"
          handleClick={() => (notice = "")}
        >
          <MaterialIcon color="fill-neutral-500">
            <Close />
          </MaterialIcon>
        </Button>
      </div>
    </Alert>
  </div>
{/if}

{#if failure}
  <div class="mt-4" role="alert">
    <Alert variant="error" Icon={ErrorIcon} onTimeout={() => (failure = "")}>
      {failure}
    </Alert>
  </div>
{/if}

<div class="people-table mt-4">
  <DataTable
    id="people-table"
    caption={`People on ${consultationData?.title ?? "this consultation"}`}
    {columns}
    {rows}
    sortable={false}
    searchable={false}
    columnSelect={false}
    striped={true}
    paginated={people.length > PAGE_SIZE}
    pageSizes={[PAGE_SIZE, 25, 50]}
    loadingCondition={loading}
    errorCondition={failedToLoad}
    loadingText="Loading people..."
    errorText="The people on this consultation could not be loaded."
    emptyText="Nobody is on this consultation yet."
  >
    {#snippet cellContent(_content, row, column)}
      {@const person = row.user}
      {#if column.key === "email"}
        <span class="flex flex-wrap items-center gap-2 text-neutral-900">
          <span>{person.email}{person.id === userData?.id ? " (you)" : ""}</span
          >
          {#if person.id === creatorId}
            <Tag>Creator</Tag>
          {/if}
        </span>
      {:else if person.id !== creatorId}
        <Button
          size="sm"
          variant="danger"
          ariaLabel={`Remove ${person.email}`}
          handleClick={() => openRemove(person)}
        >
          Remove
        </Button>
      {/if}
    {/snippet}
  </DataTable>
</div>

{#if adding && consultationData}
  <AddPeopleModal
    consultationTitle={consultationData.title}
    existingEmails={people.map((person) => person.email)}
    onClose={closeDialogs}
    onAdd={addPeople}
  />
{/if}

{#if personToRemove && consultationData}
  <RemovePersonModal
    person={personToRemove}
    consultationTitle={consultationData.title}
    onClose={closeDialogs}
    onConfirm={removePerson}
  />
{/if}

<style>
  @reference "../../../styles/global.css";

  .people-table :global(thead th) {
    @apply px-5 py-2.5;
  }

  .people-table :global(tbody td) {
    @apply px-5 py-4;
  }
</style>
