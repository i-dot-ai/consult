<script lang="ts">
  import { fade } from "svelte/transition";

  import TitleRow from "../TitleRow.svelte";
  import Panel from "../Panel/Panel.svelte";
  import DemographicGroup from "../../DemographicGroup/DemographicGroup.svelte";
  import FilterAlt from "../../svg/material/FilterAlt.svelte";
  import Switch from "../../inputs/Switch/Switch.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import Diamond from "../../svg/material/Diamond.svelte";
  import type { DemoOptionsResponseItem } from "../../../global/types";
  import Visibility from "../../svg/material/Visibility.svelte";
  import type { Component } from "svelte";

  interface Props {
    demographics: DemoOptionsResponseItem[];
    loading: boolean;
    showEvidenceRich?: boolean;
    showUnseenResponse?: boolean;
    evidenceRich?: boolean;
    setEvidenceRich?: (newVal: boolean) => void;
    unseenResponses?: boolean;
    setUnseenResponses?: (newVal: boolean) => void;
  }
  let {
    demographics = [],
    loading = true,
    showEvidenceRich = true,
    evidenceRich = false,
    setEvidenceRich = () => {},
    showUnseenResponse = false,
    unseenResponses = false,
    setUnseenResponses = () => {},
  }: Props = $props();

  let categories = $derived.by(() => {
    const grouped: Record<string, DemoOptionsResponseItem[]> = {};
    for (const item of demographics) {
      if (!grouped[item.name]) {
        grouped[item.name] = [];
      }
      grouped[item.name].push(item);
    }
    return grouped;
  });
</script>

{#snippet filter_switch(
  id: string,
  value: boolean,
  handle_change: (v: boolean) => void,
  bgColour: string,
  iconColour: string,
  text: string,
  ToggleIcon: Component,
)}
  {#snippet filterLabel()}
    <div class="flex items-center gap-1">
      <div class="rounded-2xl {bgColour} p-0.5 text-xs">
        <MaterialIcon size="1rem" color={iconColour}>
          <ToggleIcon></ToggleIcon>
        </MaterialIcon>
      </div>

      <span class="text-xs">{text}</span>
    </div>
  {/snippet}
  <Panel level={2} border={true} bg={true}>
    <Switch
      {id}
      label={filterLabel}
      {value}
      handleChange={(value: boolean) => handle_change(value)}
    />
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
        unseenResponses,
        setUnseenResponses,
        "bg-iaiteal-200",
        "fill-iaiteal-500",
        "Show unseen responses",
        Visibility,
      )}
    {/if}
    {#if loading && demographics.length === 0}
      <div in:fade>
        {#each "_".repeat(3) as _, i (i)}
          <section>
            <Panel level={2} border={true} bg={false}>
              <h3
                class="blink w-max select-none bg-neutral-100 text-neutral-100"
              >
                skeleton
              </h3>
              <div class="my-1">
                <div class="demo-filter relative w-full pb-3">
                  <div class="mb-1 grid grid-cols-3 gap-1">
                    <span
                      class="blink select-none bg-neutral-100 text-left text-neutral-100"
                      >skeleton</span
                    >
                    <span
                      class="blink select-none bg-neutral-100 text-right text-neutral-100"
                      >000%</span
                    >
                    <span
                      class="blink select-none bg-neutral-100 text-right text-neutral-100"
                      >00000</span
                    >
                  </div>
                  <div
                    class="blink w-full select-none bg-neutral-100 text-neutral-100"
                  >
                    {"_".repeat(10)}
                  </div>
                </div>
              </div>
            </Panel>
          </section>
        {/each}
      </div>
    {:else}
      <div in:fade>
        {#each Object.entries(categories) as [category, items] (category)}
          <DemographicGroup {category} {items} countsLoading={loading} />
        {/each}
      </div>
    {/if}
  </Panel>
</aside>
