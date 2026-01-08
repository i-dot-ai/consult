<script lang="ts">
  import { getPercentage } from "../../../global/utils";
  import type { RespondentDemoItem } from "../../../global/types";

  import MaterialIcon from "../../MaterialIcon.svelte";
  import Person from "../../svg/material/Person.svelte";
  import Panel from "../Panel/Panel.svelte";
  import Calendar from "../../svg/material/Calendar.svelte";

  import RespondentSidebarItem from "../RespondentSidebarItem/RespondentSidebarItem.svelte";

  export interface Props {
    demoData: RespondentDemoItem[];
    stakeholderName?: string;
    questionsAnswered: number;
    totalQuestions: number;
    updateStakeholderName?: (newStakeholderName: string) => void;
  }

  let {
    demoData = [],
    stakeholderName = "",
    questionsAnswered = 0,
    totalQuestions = 0,
    updateStakeholderName = () => {},
  }: Props = $props();
</script>

<Panel>
  <div class="mb-6 flex items-center gap-2">
    <MaterialIcon size="1.5rem" color="fill-neutral-700">
      <Person />
    </MaterialIcon>
    <h2 class="text-sm">Respondent Demographics</h2>
  </div>

  <div class="pl-4">
    {#each demoData as demoDataItem (demoDataItem.name)}
      <RespondentSidebarItem
        title={demoDataItem.name}
        subtitle={demoDataItem.value}
      />
    {/each}

    <RespondentSidebarItem
      title="Stakeholder Name"
      subtitle={stakeholderName}
      editable={true}
      updateSubtitle={updateStakeholderName}
    />

    <hr class="my-4" />

    <RespondentSidebarItem
      title="Questions Answered"
      subtitle={`${getPercentage(questionsAnswered, totalQuestions)}% (${questionsAnswered}/${totalQuestions})`}
      icon={Calendar}
    />
  </div>
</Panel>
