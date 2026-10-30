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
  import Alert from "../../Alert/Alert.svelte";
  import SkeletonText from "../../SkeletonText/SkeletonText.svelte";
  import DeleteConsultationModal from "../../DeleteConsultationModal/DeleteConsultationModal.svelte";

  import {
    buildConsultationGetQuery,
    buildConsultationRenameQuery,
  } from "../../../global/queries/consultations/queries";
  import { buildCurrentUserGetQuery } from "../../../global/queries/users/queries";
  import {
    getConsultationAnswersUrl,
    getConsultationDashboardUrl,
    getConsultationUsersUrl,
    getFinaliseThemesUrl,
    Routes,
  } from "../../../global/routes";
  import type { ConsultationStage, User } from "../../../global/types";
  import { createUserState } from "../../../global/state.svelte";
  import type {
    ConsultationV2,
    SurveyImportStatus,
  } from "../../../global/queries/consultations/types";
  import { getDataSetupActiveUrl } from "../../../global/utils";

  interface Props {
    consultationId: string;
  }

  type RenameInvalidReason = "" | "empty";

  let { consultationId = "" }: Props = $props();

  let isRenaming = $state(false);
  let isDeleting = $state(false);
  let alertText = $state("");

  const user = buildCurrentUserGetQuery();
  let userData: User = $derived(user.query?.data);

  let consultation = $derived(buildConsultationGetQuery(consultationId));
  let consultationData: ConsultationV2 | undefined = $derived(
    consultation.query.data,
  );

  let userState = $derived(createUserState(userData, consultationData));
  let userCanDelete = $derived(userState?.isOwner || userState?.isAdmin);

  let renameValue: string = $derived(consultationData?.title || "");
  let consultationRename = $derived(
    buildConsultationRenameQuery(consultationId),
  );

  let isRenameSaving = $derived(consultationRename.query.isPending);

  function getStatusText(stage: ConsultationStage | undefined) {
    if (!stage) {
      return "";
    }
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
    tagVariant: "success" | "default" | "warning" | "error";
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

  function getDataSetupPanelText(surveyImportStatus?: SurveyImportStatus) {
    if (surveyImportStatus === "import_failed") {
      return "There has been an error while importing your data.";
    } else if (surveyImportStatus === "file_uploading") {
      return "Consult is adding the responses. This can take a few hours. You can leave this page. Nothing else can start until this finishes.";
    } else if (
      surveyImportStatus === "pending_questions" ||
      surveyImportStatus === "pending_demographics"
    ) {
      return "Your file has been successfully uploaded. Please proceed with setting up your data.";
    } else if (surveyImportStatus === "import_complete") {
      return "The data import has been completed.";
    }
    return "The responses are not uploaded yet.";
  }
  function getDataSetupButtonText(surveyImportStatus?: SurveyImportStatus) {
    if (
      surveyImportStatus === "file_uploading" ||
      surveyImportStatus === "import_failed" ||
      surveyImportStatus === "import_complete"
    ) {
      // do not render button for certain statuses
      return "";
    } else if (surveyImportStatus !== "not_started") {
      return "Continue setting up data";
    }
    return "Set up the data";
  }
  function getDataSetupTagVariant(surveyImportStatus?: SurveyImportStatus) {
    if (
      surveyImportStatus === "file_uploading" ||
      surveyImportStatus === "import_complete"
    ) {
      return "default";
    } else if (surveyImportStatus === "import_failed") {
      return "error";
    }
    return "warning";
  }

  const CONTENT: Record<string, ContentData> = $derived({
    analysis: {
      panelText:
        "Every response is assigned to a theme. Check the assignments before you report.",
      panelButtonText: "View Dashboard",
      panelButtonUrl: getConsultationDashboardUrl(consultationId),
      tagVariant: "success",
      adminLinks: [MANAGE_PEOPLE_LINK, VIEW_RESPONSES_LINK],
      ownerLinks: [MANAGE_PEOPLE_LINK, VIEW_RESPONSES_LINK],
      userLinks: [WHO_CAN_SEE_LINK, VIEW_RESPONSES_LINK],
    },
    assigning_themes: {
      panelText:
        "Consult is assigning every response to the finalised themes. This can take more than 20 minutes. Nothing else can start until this finishes.",
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
        "Consult is reading the responses and finding themes. This can take more than 20 minutes. Nothing else can start until this finishes.",
      tagVariant: "default",
      adminLinks: [MANAGE_PEOPLE_LINK, VIEW_RESPONSES_LINK],
      ownerLinks: [MANAGE_PEOPLE_LINK, VIEW_RESPONSES_LINK],
      userLinks: [WHO_CAN_SEE_LINK, VIEW_RESPONSES_LINK],
    },
    setup: {
      panelText: getDataSetupPanelText(consultationData?.survey_import_status),
      panelButtonText: getDataSetupButtonText(
        consultationData?.survey_import_status,
      ),
      panelButtonUrl: getDataSetupActiveUrl(
        consultationId,
        consultationData?.survey_import_status,
      ),
      tagVariant: getDataSetupTagVariant(
        consultationData?.survey_import_status,
      ),
      adminLinks: [MANAGE_PEOPLE_LINK],
      ownerLinks: [MANAGE_PEOPLE_LINK],
      userLinks: [WHO_CAN_SEE_LINK],
    },
  } as const);

  let content = $derived(CONTENT[consultationData?.stage || 0] || {});
  let links = $derived.by(() => {
    if (userState?.isAdmin) {
      return content.adminLinks;
    }
    if (userState?.isOwner) {
      return content.ownerLinks;
    }
    return content.userLinks;
  });

  function validateRenameValue(value: string): RenameInvalidReason {
    if (!value) {
      return "empty";
    }
    return "";
  }

  async function handleSubmitRename(event: Event) {
    event.preventDefault();

    const ERROR_TEXT = "Something went wrong while renaming this consultation.";

    // Validate new consultation title value
    const invalidReason = validateRenameValue(renameValue);
    if (invalidReason) {
      if (invalidReason === "empty") {
        alertText = "New consultation name cannot be empty";
      } else {
        alertText = "New consultation name is invalid";
      }
      return;
    }

    // Handle if server returns an error status code
    try {
      await consultationRename.fetch({ body: { title: renameValue } });
    } catch {
      alertText = ERROR_TEXT;
    }

    // Handle if fetch itself errors
    if (consultationRename.query.isError) {
      alertText = ERROR_TEXT;
    }

    // Refresh consultation
    await consultation.fetch({});

    // Toggle off renaming state
    isRenaming = false;
  }
</script>

<section>
  {#if alertText}
    <div transition:fade>
      <Alert variant="error" onTimeout={() => (alertText = "")}>
        <div class="flex justify-between gap-2">
          {alertText}

          <Button variant="ghost" handleClick={() => (alertText = "")}>
            <MaterialIcon color="fill-neutral-500">
              <Close />
            </MaterialIcon>
          </Button>
        </div>
      </Alert>
    </div>
  {/if}
</section>

<div class="mt-8 mb-4">
  <Link href={Routes.Consultations} ariaLabel="Back to all consultations">
    Back to Consultations
  </Link>
</div>

<section>
  <div class="flex gap-2 items-center">
    {#if isRenaming}
      <form
        class="w-full flex gap-2 items-center"
        onsubmit={handleSubmitRename}
      >
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
          <Button
            variant="primary"
            size="sm"
            handleClick={handleSubmitRename}
            disabled={isRenameSaving}
          >
            <div class="text-xs flex gap-1 items-center">
              <MaterialIcon color="fill-white">
                <Check />
              </MaterialIcon>

              {#if isRenameSaving}
                Saving
              {:else}
                Save
              {/if}
            </div>
          </Button>
        </div>
      </form>
    {:else}
      <Title level={2}>
        {#if consultation.query.isPending}
          <SkeletonText length={3} />
        {:else}
          {consultationData?.title}
        {/if}
      </Title>
    {/if}

    <div class="my-auto flex gap-2">
      <Button
        handleClick={() => (isRenaming = !isRenaming)}
        variant="gray"
        size="sm"
        highlighted={isRenaming}
        highlightVariant="none"
        disabled={isRenameSaving}
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
    {#if user.query.isPending || consultation.query.isPending}
      <SkeletonText length={7} />
    {:else}
      Created by {userState?.createdByText} on {userState?.createdAtText}. {consultationData
        ?.users.length === 1
        ? "Only you can see it so far."
        : `${consultationData?.users.length} people can see it.`}
    {/if}
  </p>
</section>

<section>
  <Panel>
    <div class="pt-2 pb-8 px-2">
      <div class="mb-3">
        <Tag variant={content.tagVariant}>
          {getStatusText(consultationData?.stage)}
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
            href={content.panelButtonUrl || "#"}
          >
            {content.panelButtonText}
          </Button>
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
  onError={() => {
    isDeleting = false;
    alertText = "Something went wrong while deleting this consultation.";
  }}
  onSuccess={() => {
    isDeleting = false;
    window.location.href = Routes.Consultations;
  }}
/>
