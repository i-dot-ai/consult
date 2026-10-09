<script lang="ts">
  import { fade } from "svelte/transition";

  import Button from "../../inputs/Button/Button.svelte";
  import Title from "../../Title.svelte";
  import Link from "../../Link.svelte";
  import Tag from "../../Tag/Tag.svelte";
  import TextInput from "../../inputs/TextInput/TextInput.svelte";
  import Panel from "../../dashboard/Panel/Panel.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import Check from "../../svg/material/Check.svelte";
  import Close from "../../svg/material/Close.svelte";
  import EditSquare from "../../svg/material/EditSquare.svelte";
  import Delete from "../../svg/material/Delete.svelte";

  import { buildConsultationGetQuery } from "../../../global/queries/consultations/queries";
  import { buildCurrentUserGetQuery } from "../../../global/queries/users/queries";
  import {
    getConsultationAnswersUrl,
    getConsultationDetailUrl,
    getConsultationUsersUrl,
    getDataUploadUrl,
    getFinaliseThemesUrl,
    Routes,
  } from "../../../global/routes";
  import type {
    Consultation,
    ConsultationStage,
    User,
  } from "../../../global/types";
  import DeleteConsultationModal from "../../DeleteConsultationModal/DeleteConsultationModal.svelte";

  interface Props {
    consultationId: string;
  }

  let { consultationId = "" }: Props = $props();

  let isRenaming = $state(false);
  let isDeleting = $state(false);

  const user = buildCurrentUserGetQuery();
  let consultation = $derived(buildConsultationGetQuery(consultationId));
  let consultationData: Consultation = $derived(consultation.query?.data);
  let renameValue: string = $derived(consultationData?.title || "");

  let createdByEmail = $derived.by(() => {
    const createdBy = consultationData?.created_by;
    return typeof createdBy === "string" ? createdBy : createdBy?.email;
  });
  let userIsOwner = $derived(user.query?.data?.email === createdByEmail);
  let userIsAdmin = $derived(user.query?.data?.is_staff);
  let userCanDelete = $derived(
    user.query?.data?.is_staff || userIsOwner || userIsAdmin,
  );

  function getCreatedByText(createdBy: User | string | null) {
    if (!createdByEmail) {
      return "an unknown user";
    }
    if (userIsOwner) {
      return "you";
    }
    // TODO: to avoid merge conflict. Remove type cast after ConsultationList pr is merged.
    return createdByEmail || createdBy;
  }
  function getCreatedAtText(created_at: string) {
    return new Date(created_at).toLocaleDateString();
  }
  function getStatusText(stage: ConsultationStage) {
    return (stage.charAt(0).toUpperCase() + stage.slice(1)).replaceAll(
      "_",
      " ",
    );
  }

  interface ContentDataLink {
    url: string;
    text: string;
    description: string;
  }

  interface ContentData {
    panelText: string;
    panelButtonText?: string;
    panelButtonUrl?: string;
    tagVariant: "success" | "default" | "warning";
    ownerLinks?: ContentDataLink[];
    userLinks?: ContentDataLink[];
    adminLinks?: ContentDataLink[];
  }

  const MANAGE_PEOPLE_LINK = $derived({
    text: "Manage people",
    description: "Add and remove people on this consultation",
    url: getConsultationUsersUrl(consultationId),
  });

  const WHO_CAN_SEE_LINK = $derived({
    text: "Who can see this",
    description: "Everyone on a consultation can see who else is on it",
    url: getConsultationUsersUrl(consultationId),
  });

  const VIEW_RESPONSES_LINK = $derived({
    text: "View all responses",
    description: "Every response, as it was uploaded",
    url: getConsultationAnswersUrl(consultationId),
  });

  const CONTENT: Record<string, ContentData> = $derived({
    analysis: {
      panelText:
        "Every response is assigned to a theme. Check the assignments before you report.",
      panelButtonText: "View Dashboard",
      panelButtonUrl: getConsultationDetailUrl(consultationId),
      tagVariant: "success",
      adminLinks: [MANAGE_PEOPLE_LINK, VIEW_RESPONSES_LINK],
      ownerLinks: [MANAGE_PEOPLE_LINK, VIEW_RESPONSES_LINK],
      userLinks: [WHO_CAN_SEE_LINK, VIEW_RESPONSES_LINK],
    },
    assigning_themes: {
      panelText:
        "Consult is assigning every response to the finalised themes. This can take more than 20 minutes.",
      tagVariant: "default",
      adminLinks: [MANAGE_PEOPLE_LINK, VIEW_RESPONSES_LINK],
      ownerLinks: [MANAGE_PEOPLE_LINK, VIEW_RESPONSES_LINK],
      userLinks: [WHO_CAN_SEE_LINK, VIEW_RESPONSES_LINK],
    },
    finalising_themes: {
      panelText:
        "Themes found by the AI are ready to check. No response is assigned to a theme until you finalise them.",
      panelButtonText: "Finalise themes",
      panelButtonUrl: getFinaliseThemesUrl(consultationId),
      tagVariant: "warning",
      adminLinks: [MANAGE_PEOPLE_LINK, VIEW_RESPONSES_LINK],
      ownerLinks: [MANAGE_PEOPLE_LINK, VIEW_RESPONSES_LINK],
      userLinks: [WHO_CAN_SEE_LINK, VIEW_RESPONSES_LINK],
    },
    finding_themes: {
      panelText:
        "Consult is reading the responses and finding themes. This can take more than 20 minutes.",
      tagVariant: "default",
      adminLinks: [MANAGE_PEOPLE_LINK, VIEW_RESPONSES_LINK],
      ownerLinks: [MANAGE_PEOPLE_LINK, VIEW_RESPONSES_LINK],
      userLinks: [WHO_CAN_SEE_LINK, VIEW_RESPONSES_LINK],
    },
    setup: {
      panelText: "The responses are not uploaded yet.",
      panelButtonText: "Set up the data",
      panelButtonUrl: getDataUploadUrl(consultationId),
      tagVariant: "warning",
      adminLinks: [MANAGE_PEOPLE_LINK],
      ownerLinks: [MANAGE_PEOPLE_LINK],
      userLinks: [WHO_CAN_SEE_LINK],
    },
  } as const);

  let content = $derived(CONTENT[consultationData?.stage] || {});
  let links = $derived.by(() => {
    if (userIsAdmin) {
      return content.adminLinks;
    }
    if (userIsOwner) {
      return content.ownerLinks;
    }
    return content.userLinks;
  });
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

      {#if userCanDelete && !isRenaming}
        <Button variant="danger" handleClick={() => (isDeleting = true)}>
          <div class="flex gap-1 items-center text-xs delete-button">
            <MaterialIcon color="fill-red-700">
              <Delete />
            </MaterialIcon>

            Delete
          </div>
        </Button>
      {/if}
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

<section>
  <Panel>
    <div class="pt-2 pb-8 px-2">
      <div class="mb-3">
        <Tag variant={content.tagVariant}>
          {getStatusText(consultationData?.stage || "")}
        </Tag>
      </div>

      <p class="text-neutral-700 text-sm">
        {content.panelText}
      </p>

      <div class="mt-4">
        {#if content.panelButtonText}
          <Button
            variant="primary"
            size="sm"
            handleClick={() => {
              if (!content.panelButtonUrl) {
                return;
              }
              window.location.href = content.panelButtonUrl;
            }}
          >
            {content.panelButtonText}
          </Button>
        {:else}
          <p class="text-neutral-700 text-sm">
            Nothing else can start until this finishes.
          </p>
        {/if}
      </div>
    </div>
  </Panel>
</section>

{#if links}
  <section>
    <Title level={3}>
      <span class="font-[500]">This consultation</span>
    </Title>

    {#each links as link, i (i)}
      <hr class="my-2" />

      <div class="my-3 ml-2">
        <Link href={link.url} ariaLabel={link.description}>
          {link.text}
        </Link>

        <p class="text-sm text-neutral-500">{link.description}</p>
      </div>
    {/each}
  </section>
{/if}

<DeleteConsultationModal
  consultation={isDeleting ? consultationData : undefined}
  onClose={() => (isDeleting = false)}
  onError={(consultation) => {
    console.log("ERROR");
    isDeleting = false;
  }}
  onSuccess={(consultation) => {
    console.log("SUCCESS");
    isDeleting = false;
  }}
/>
