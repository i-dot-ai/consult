<script lang="ts">
  import { fade } from "svelte/transition";

  import TitleRow from "../TitleRow.svelte";
  import Panel from "../Panel/Panel.svelte";
  import DemoFilter from "../../DemoFilter/DemoFilter.svelte";
  import FilterAlt from "../../svg/material/FilterAlt.svelte";
  import Switch from "../../inputs/Switch/Switch.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import Diamond from "../../svg/material/Diamond.svelte";
  import type {
    DemoData,
    DemoOption,
    DemoOptionsResponse,
    DemoTotalCounts,
  } from "../../../global/types";
  import Visibility from "../../svg/material/Visibility.svelte";
  import type { Component } from "svelte";

  interface Props {
    demoOptions: DemoOption;
    demoData: DemoData;
    demoOptionsData?: DemoOptionsResponse;
    loading: boolean;
    showEvidenceRich?: boolean;
    showUnseenResponse?: boolean;
    evidenceRich?: boolean;
    setEvidenceRich?: (newVal: boolean) => void;
    unseenResponsesOnly?: boolean;
    setUnseenResponses?: (newVal: boolean) => void;
  }
  let {
    demoOptions = {},
    demoData = {},
    demoOptionsData = [],
    loading = true,
    showEvidenceRich = true,
    evidenceRich = false,
    setEvidenceRich = () => {},
    showUnseenResponse = false,
    unseenResponsesOnly = false,
    setUnseenResponses = () => {},
  }: Props = $props();

  // Derive to avoid calculating on re-render
  let totalCounts: DemoTotalCounts = $derived.by(() => {
    let counts: Record<string, number> = {};
    for (const category of Object.keys(demoData)) {
      counts[category] = Object.values(demoData[category]).reduce(
        (a, b) => (a as number) + (b as number),
        0, //  initial value
      );
    }
    return counts;
  });
</script>

{#snippet filter_switch(
  id: string,
  label: string,
  value: boolean,
  handle_change: (v: boolean) => void,
  bgColour: string,
  iconColour: string,
  text: string,
  ToggleIcon: Component,
)}
  <Panel level={2} border={true} bg={true}>
    <Switch
      {id}
      {label}
      {value}
      handleChange={(value: boolean) => handle_change(value)}
    >
      <div slot="label" class="flex items-center gap-1">
        <div class="rounded-2xl {bgColour} p-0.5 text-xs">
          <MaterialIcon size="1rem" color={iconColour}>
            <ToggleIcon></ToggleIcon>
          </MaterialIcon>
        </div>

        <span class="text-xs">{text}</span>
      </div>
    </Switch>
  </Panel>
{/snippet}

<aside>
  <Panel>
    <TitleRow level={2} title="Filters" subtitle="">
      <FilterAlt slot="icon" />
    </TitleRow>

    {#if showEvidenceRich}
      {@render filter_switch(
        "evidence-rich-toggle",
        "Evidence rich",
        evidenceRich,
        setEvidenceRich,
        "bg-yellow-100",
        "fill-yellow-700",
        "Show evidence rich",
        Diamond,
      )}
    {/if}
    {#if showUnseenResponse}
      {@render filter_switch(
        "unseen-responses-toggle",
        "Show unseen responses",
        unseenResponsesOnly,
        setUnseenResponses,
        "bg-iaiteal-200",
        "fill-iaiteal-500",
        "Show unseen responses",
        Visibility,
      )}
    {/if}
    {#if loading}
      <div in:fade>
        {#each "_".repeat(3) as _, i (i)}
          <DemoFilter skeleton={true} />
        {/each}
      </div>
    {:else}
      <div in:fade>
        {#each Object.keys(demoOptions) as category (category)}
          <DemoFilter
            {category}
            {demoOptions}
            {demoData}
            {demoOptionsData}
            {totalCounts}
            skeleton={loading}
          />
        {/each}
      </div>
    {/if}
  </Panel>
</aside>
