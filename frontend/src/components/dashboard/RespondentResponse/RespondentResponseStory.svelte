<script lang="ts">
  import Switch from "../../inputs/Switch/Switch.svelte";
  import TextInput from "../../inputs/TextInput/TextInput.svelte";
  import RespondentResponse from "./RespondentResponse.svelte";

  let consultationId = $state("123");
  let questionId = $state("456");
  let questionTitle = $state(
    "Do you agree with the proposal to align the flavour categories of chocolate bars as outlined in the draft guidelines of the Chocolate Bar Regulation for the United Kingdom?",
  );
  let questionNumber = $state(1);
  let responseText = $state(
    "I agree in principle, but I think the guidelines should include a provision for periodic review to adapt to market changes.",
  );
  let themes = $state(["Innovation", "Standardized framework"]);
  let evidenceRich = $state(true);
</script>

<RespondentResponse
  {consultationId}
  {questionId}
  {questionTitle}
  {questionNumber}
  {responseText}
  multiChoice={[]}
  {themes}
  {evidenceRich}
/>

<hr class="my-8" />

<TextInput
  id="input-consultation-id"
  label="Consultation ID"
  value={consultationId}
  setValue={(newValue) => (consultationId = newValue)}
/>

<TextInput
  id="input-question-id"
  label="Question ID"
  value={questionId}
  setValue={(newValue) => (questionId = newValue)}
/>

<TextInput
  id="input-question-title"
  label="Question Title"
  value={questionTitle}
  setValue={(newValue) => (questionTitle = newValue)}
/>

<TextInput
  id="input-question-number"
  label="Question Number"
  value={questionNumber.toString()}
  setValue={(newValue) => (questionNumber = parseInt(newValue))}
/>

<TextInput
  id="input-response-text"
  label="Response Text"
  value={responseText}
  setValue={(newValue) => (responseText = newValue)}
/>

<TextInput
  id="input-themes-all"
  label="Themes"
  value="[ &quot;Innovation&quot;, &quot;Standardized framework&quot; ]"
  setValue={(newValue) => {
    themes = JSON.parse(newValue);
  }}
/>

<div class="w-max">
  <Switch
    id="evidence-rich-input"
    label="Evidence-rich"
    value={evidenceRich}
    handleChange={(newVal) => (evidenceRich = newVal)}
  />
</div>
