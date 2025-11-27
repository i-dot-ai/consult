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

  interface Props {
    demoOptions: DemoOption;
    demoData: DemoData;
    demoOptionsData?: DemoOptionsResponse;
    loading: boolean;
    showEvidenceRich?: boolean;
    showUnseenResponse?: boolean;
    evidenceRich?: boolean;
    setEvidenceRich?: (newVal: boolean) => void;
    unseenResponses?: boolean;
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
    showUnseenResponse = true,
    unseenResponses = false,
    setUnseenResponses = () => {},
  }: Props = $props();

  // Derive to avoid calculating on re-render
  let totalCounts: DemoTotalCounts = $derived.by(() => {
    let counts: any = {};
    for (const category of Object.keys(demoData)) {
      counts[category] = Object.values(demoData[category]).reduce(
        (a, b) => (a as number) + (b as number),
        0, //  initial value
      );
    }
    return counts;
  });
</script>

<aside>
  <Panel>
    <TitleRow level={2} title="Filters" subtitle="">
      <FilterAlt slot="icon" />
    </TitleRow>

    {#if showEvidenceRich}
      <Panel level={2} border={true} bg={true}>
        <Switch
          id="evidence-rich-toggle"
          label="Evidence Rich"
          value={evidenceRich}
          handleChange={(value: boolean) => setEvidenceRich(value)}
        >
          <div slot="label" class="flex gap-1 items-center">
            <div class="bg-yellow-100 rounded-2xl text-xs p-0.5">
              <MaterialIcon size="1rem" color="fill-yellow-700">
                <Diamond />
              </MaterialIcon>
            </div>

            <span class="text-xs">Show evidence rich</span>
          </div>
        </Switch>
      </Panel>
    {/if}
    {#if showUnseenResponse}
    <Panel level={2} border={true} bg={true}>
        <Switch
          id="unseen-responses-toggle"
          label="Show unseen responses"
          value={unseenResponses}
          handleChange={(value: boolean) => setUnseenResponses(value)}
        >
          <div slot="label" class="flex gap-1 items-center">
            <div class="bg-green-100 rounded-2xl text-xs p-0.5">
              <MaterialIcon size="1rem" color="fill-green-700">
                <Visibility />
              </MaterialIcon>
            </div>

            <span class="text-xs">Show unseen responses</span>
          </div>
        </Switch>
      </Panel>
    {/if}
    {#if loading}
      <div in:fade>
        {#each "_".repeat(3) as _}
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
