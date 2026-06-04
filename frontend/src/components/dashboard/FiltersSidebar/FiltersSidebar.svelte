<script lang="ts">
  import { fade } from "svelte/transition";

  import TitleRow from "../TitleRow.svelte";
  import Panel from "../Panel/Panel.svelte";
  import DemographicGroup from "../../DemographicGroup/DemographicGroup.svelte";
  import FilterAlt from "../../svg/material/FilterAlt.svelte";
  import type { DemoOptionsResponseItem } from "../../../global/types";

  interface Props {
    demographics: DemoOptionsResponseItem[];
    loading: boolean;
  }
  let { demographics = [], loading = true }: Props = $props();

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

<aside>
  <Panel>
    <TitleRow level={2} title="Filters" subtitle="">
      <FilterAlt slot="icon" />
    </TitleRow>
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
