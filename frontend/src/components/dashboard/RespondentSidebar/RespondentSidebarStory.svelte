<script lang="ts">
  import TextInput from "../../inputs/TextInput/TextInput.svelte";
  import RespondentSidebar, {
    type RespondentDemoItem,
  } from "./RespondentSidebar.svelte";

  let demoData: RespondentDemoItem[] = [
    { name: "Country", value: "England" },
    { name: "Age", value: "25-35" },
  ];
  let stakeholderName: string = $state("Test stakeholder");
  let questionsAnswered: number = $state(8);
  let totalQuestions: number = $state(10);
</script>

<RespondentSidebar
  {demoData}
  {stakeholderName}
  {questionsAnswered}
  {totalQuestions}
  updateStakeholderName={(newStakeholderName) =>
    (stakeholderName = newStakeholderName)}
/>

<hr class="my-8" />

<TextInput
  id="input-stakeholderName"
  label="Stakeholder Name"
  value={stakeholderName}
  setValue={(newValue) => (stakeholderName = newValue)}
/>

<TextInput
  id="input-questions-answered"
  label="Questions Answered"
  value={questionsAnswered.toString()}
  setValue={(newValue) => (questionsAnswered = parseInt(newValue))}
/>

<TextInput
  id="input-total-questions"
  label="Total Questions"
  value={totalQuestions.toString()}
  setValue={(newValue) => (totalQuestions = parseInt(newValue))}
/>
