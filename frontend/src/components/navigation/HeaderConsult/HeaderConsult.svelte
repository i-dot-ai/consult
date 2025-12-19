<script lang="ts">
  import { slide } from "svelte/transition";

  import { Routes } from "../../../global/routes";
  import type { ConsultationStage } from "../../../global/types";

  import Button from "../../inputs/Button/Button.svelte";
  import Breadcrumbs from "../Breadcrumbs/Breadcrumbs.svelte";
  import Header from "../Header/Header.svelte";
  import ConsultIcon from "../../svg/ConsultIcon.svelte";
  import ProfileButton from "../ProfileButton/ProfileButton.svelte";

  interface Props {
    subtitle?: string;
    path?: string;
    isSignedIn: boolean;
    isStaff?: boolean;
    showProcess?: boolean;
    consultationId?: string;
    consultationStage?: ConsultationStage;
  }

  let {
    subtitle,
    path,
    isSignedIn,
    isStaff,
    showProcess,
    consultationId,
    consultationStage,
  }: Props = $props();

  let showBreadcrumbs = $state(false);
</script>

<Header
  title="Consult"
  {subtitle}
  icon={ConsultIcon}
  pathParts={path ? [path] : []}
  navItems={[
    {
      label: "Support",
      children: [{ label: "Privacy notice", url: Routes.Privacy }],
    },

    // only show if user is staff
    ...(isStaff
      ? [
          {
            label: "Manage",
            children: [
              {
                label: "Manage Consultations",
                url: Routes.SupportConsultations,
              },
              { label: "Manage Users", url: Routes.SupportUsers },
            ],
          },
        ]
      : []),
  ]}
>
  {#snippet endItems()}
    <div class="flex items-end gap-1">
      {#if showProcess}
        <div class="my-auto ml-2 md:ml-0">
          <Button
            size="sm"
            variant="ghost"
            highlighted={showBreadcrumbs}
            highlightVariant="primary"
            handleClick={() => (showBreadcrumbs = !showBreadcrumbs)}
            ariaControls="breadcrumbs-panel"
          >
            Process
          </Button>
        </div>
      {/if}

      <ProfileButton {isSignedIn} />
    </div>
  {/snippet}
</Header>

<!-- wrapper required for transition -->
<div id="breadcrumbs-panel">
  {#if showProcess && showBreadcrumbs}
    <div transition:slide class="py-2 shadow-lg">
      <Breadcrumbs {consultationId} {consultationStage} />
    </div>
  {/if}
</div>
