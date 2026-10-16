<script lang="ts">
  import { createRawSnippet } from "svelte";
  import type { Component, Snippet } from "svelte";
  import { fade } from "svelte/transition";

  import Panel from "../../../dashboard/Panel/Panel.svelte";
  import Button from "../../../inputs/Button/Button.svelte";
  import Title from "../../../Title.svelte";
  import Alert from "../../../Alert/Alert.svelte";
  import Timeline from "../../../Timeline/Timeline.svelte";
  import MaterialIcon from "../../../MaterialIcon.svelte";
  import Check from "../../../svg/material/Check.svelte";
  import Description from "../../../svg/material/Description.svelte";
  import Upload from "../../../svg/material/Upload.svelte";
  import SelectCheckBox from "../../../svg/material/SelectCheckBox.svelte";
  import Tune from "../../../svg/material/Tune.svelte";
  import Download from "../../../svg/material/Download.svelte";
  import OpenInNew from "../../../svg/material/OpenInNew.svelte";
  import SkeletonText from "../../../SkeletonText/SkeletonText.svelte";

  import { buildConsultationGetQuery } from "../../../../global/queries/consultations/queries";
  import { buildCurrentUserGetQuery } from "../../../../global/queries/users/queries";
  import { createUserState } from "../../../../global/state.svelte";
  import {
    getConsultationUsersUrl,
    getDataUploadStepOneUrl,
  } from "../../../../global/routes";

  interface Props {
    consultationId: string;
  }

  let { consultationId }: Props = $props();

  const consultation = $derived(buildConsultationGetQuery(consultationId));
  const consultationData = $derived(consultation.query.data);
  const user = buildCurrentUserGetQuery();
  const userData = $derived(user.query?.data);

  let userState = $derived(createUserState(userData, consultationData));
</script>

{#snippet infoItem(content: Snippet, Icon: Component)}
  <div class="flex items-start gap-4 mb-6">
    <div class="shrink-0">
      <MaterialIcon color="fill-secondary" size="1.5rem">
        <Icon />
      </MaterialIcon>
    </div>
    <p class="text-md text-neutral-700">
      {@render content()}
    </p>
  </div>
{/snippet}

<section class="mb-6">
  <Title level={1}>
    <span class="text-2xl">Upload and check the responses</span>
  </Title>

  <div class="-mt-2">
    <Panel variant="gray" bg={true}>
      <div class="flex justify-between items-center gap-4">
        <div>
          <Title level={2}>
            <span class="text-md">
              {#if user.query.isPending || consultation.query.isPending}
                <SkeletonText length={2} />
              {:else if user.query.isError || consultation.query.isError}
                <Alert variant="error">Error while loading consultation data</Alert>
              {:else}
                <span in:fade>{consultation.query.data?.title}</span>
              {/if}
            </span>
          </Title>
          <p class="text-md text-neutral-500">
            {#if user.query.isPending || consultation.query.isPending}
              <SkeletonText length={5} />
            {:else if user.query.isError || consultation.query.isError}
              <!-- Do not render anything -->
            {:else}
              <span in:fade>Created by {userState?.createdByText} on {userState?.createdAtText}.</span>
            {/if}
          </p>
        </div>

        <div class="my-auto">
          <Button
            size="sm"
            handleClick={() =>
              (window.location.href = getConsultationUsersUrl(consultationId))}
            ariaLabel="View who can see this consultation"
            title="View who can see this consultation"
          >
            {userState?.isOwner || userState?.isAdmin ? "Manage people" : "Who can see this"}
          </Button>
        </div>
      </div>
    </Panel>
  </div>

  <p class="text-neutral-500 text-md my-6">
    Consult analyses files of consultation responses. These five steps upload
    the file, check it and confirm the question type.
  </p>

  <Panel>
    <Title level={2}>
      <span class="text-lg">Importance of getting this set up right</span>
    </Title>

    <p class="text-neutral-500 text-md my-6">
      Every question is either open, closed or hybrid and that impacts the
      format in the app
    </p>

    {@render infoItem(
      createRawSnippet(() => ({
        render: () => `
          <p>
            <strong>Open questions</strong> are free text. Consult reads every answer and groups them into themes, which can then be edited, merged and signed off. Those themes allow for analysis.
          </p>
        `,
      })),
      Check,
    )}

    {@render infoItem(
      createRawSnippet(() => ({
        render: () => `
          <p>
            <strong>Closed questions</strong> have a fixed set of answers. Consult enables these answers to act as filters, so you can read the themes for one sector, region or respondent type at a time.
          </p>
        `,
      })),
      Check,
    )}
  </Panel>
</section>

<section class="mb-6">
  <Panel>
    <Title level={2}>The five steps</Title>

    <p class="text-neutral-500 text-sm mt-4 mb-8">
      The first two happen in your survey tool and your spreadsheet. They are
      part of the job, so they are listed here with the rest.
    </p>

    <Timeline
      items={[
        {
          Icon: Download,
          TagIcon: OpenInNew,
          smallText: "Step 1",
          titleText: "Export the responses",
          tagText: "Happens outside Consult",
          bodyText: "Get your data out of Qualtrics or Citizen Space",
        },
        {
          Icon: Description,
          TagIcon: OpenInNew,
          smallText: "Step 2",
          titleText: "Prepare your file",
          tagText: "Happens outside Consult",
          bodyText:
            "Set it up in the right way for Consult, and remove personal information if needed",
        },
        {
          Icon: Upload,
          smallText: "Step 3",
          titleText: "Upload your file",
          bodyText:
            "Provided data is in the correct format, Consult uploads it into the app",
        },
        {
          Icon: SelectCheckBox,
          smallText: "Step 4",
          titleText: "Review your questions",
          bodyText: "Confirm whether each question is open, closed or hybrid",
        },
        {
          Icon: Tune,
          smallText: "Step 5",
          titleText: "Set up your closed questions",
          bodyText: "Choose which ones become filters on your dashboard",
        },
      ]}
    />
  </Panel>
</section>

<section class="mb-6">
  <Panel>
    <div class="mb-6">
      <Title level={2}>
        <span class="text-lg">Before you start</span>
      </Title>
    </div>

    {@render infoItem(
      createRawSnippet(() => ({
        render: () => `
          <p>
            Responses should be in a single <strong>.xlsx</strong> or <strong>.csv</strong> file. Step 1 shows how to export.
          </p>
        `,
      })),
      Check,
    )}

    {@render infoItem(
      createRawSnippet(() => ({
        render: () => `
          <p>
            Nothing is analysed until step 5 is completed.
          </p>
        `,
      })),
      Check,
    )}

    <Panel variant="gray" bg={true}>
      <div class="flex gap-4 flex-wrap sm:flex-nowrap">
        <Title level={4}>Still collecting responses?</Title>
        <p class="text-sm text-neutral-500">
          Start anyway. Steps 1 and 2 tell you what a usable file looks like,
          which is far easier to act on before your consultation closes than
          after.
        </p>
      </div>
    </Panel>
  </Panel>
</section>

<section>
  <div class="flex justify-end">
    <Button
      size="sm"
      variant="primary"
      handleClick={() =>
        (window.location.href = getDataUploadStepOneUrl(consultationId))}
      title="Go to Step 1 of Survey Import"
      ariaLabel="Go to Step 1 of Survey Import"
    >
      Start step 1: export the responses
    </Button>
  </div>
</section>
