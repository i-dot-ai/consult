<script lang="ts">
  import { fade } from "svelte/transition";

  import { buildConsultationGetQuery } from "../../../global/queries/consultations/queries";
  import { buildCurrentUserGetQuery } from "../../../global/queries/users/queries";
  import type { User } from "../../../global/types";
  import Button from "../../inputs/Button/Button.svelte";
  import TextInput from "../../inputs/TextInput/TextInput.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import Check from "../../svg/material/Check.svelte";
  import Close from "../../svg/material/Close.svelte";
  import EditSquare from "../../svg/material/EditSquare.svelte";
  import Title from "../../Title.svelte";
  import Link from "../../Link.svelte";
  import { Routes } from "../../../global/routes";

  interface Props {
    consultationId: string;
  }

  let { consultationId = "" }: Props = $props();

  let isRenaming = $state(false);

  const user = buildCurrentUserGetQuery();
  let consultation = $derived(buildConsultationGetQuery(consultationId));
  let consultationData = $derived(consultation.query?.data);
  let renameValue = $derived(consultationData?.title || "");

  function getCreatedByText(createdBy: User | null) {
    if (!createdBy) {
      return "an unknown user";
    }
    const createdByEmail = createdBy?.email;
    if (user.query?.data?.email === createdByEmail) {
      return "you";
    }
    // TODO: to avoid merge conflict. Remove type cast after ConsultationList pr is merged.
    return createdByEmail || createdBy;
  }
  function getCreatedAtText(created_at: string) {
    return new Date(created_at).toLocaleDateString();
  }
</script>

<div class="mt-8 mb-4">
  <Link href={Routes.Consultations} ariaLabel="Back to all consultations">
    Back to Consultations
  </Link>
</div>

<section>
  <div class="flex gap-2 items-center">
    {#if isRenaming}
      <div class="grow">
        <TextInput
          id="rename-input"
          value={renameValue}
          setValue={(newValue) => (renameValue = newValue)}
          label="New consultation name"
          hideLabel={true}
        />
      </div>
      <div class="my-auto" in:fade>
        <Button variant="primary" size="sm">
          <div class="text-xs flex gap-1 items-center">
            <MaterialIcon color="fill-white">
              <Check />
            </MaterialIcon>

            Save
          </div>
        </Button>
      </div>
    {:else}
      <Title level={2}>
        {consultationData?.title}
      </Title>
    {/if}

    <div class="my-auto">
      <Button
        handleClick={() => (isRenaming = !isRenaming)}
        variant="gray"
        size="sm"
        highlighted={isRenaming}
        highlightVariant="none"
      >
        <div class="flex gap-1 items-center text-xs">
          <MaterialIcon color="fill-neutral-500">
            {#if isRenaming}
              <Close />
            {:else}
              <EditSquare />
            {/if}
          </MaterialIcon>

          {isRenaming ? "Cancel" : "Rename"}
        </div>
      </Button>
    </div>
  </div>

  {#if isRenaming}
    <small transition:fade class="text-neutral-500 text-xs mt-2">
      Use the name it was published under, so your team can find it.
    </small>
  {/if}

  <p class="text-neutral-500 text-sm mt-2">
    Created by {getCreatedByText(consultationData?.created_by)} on {getCreatedAtText(
      consultationData?.created_at,
    )}. {consultationData?.users.length === 1
      ? "Only you can see it so far."
      : `${consultationData?.users.length} people can see it.`}
  </p>
</section>
