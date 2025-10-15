<script lang="ts">
  import TextInput from "../../inputs/TextInput/TextInput.svelte";
  import RespondentTopbar from "./RespondentTopbar.svelte";

  let respondentId = $state("4815");
</script>

<RespondentTopbar
  title={`Respondend ${respondentId}`}
  backText="Back to Analysis"
/>

<hr class="my-8" />

<TextInput
  id="input-respondent-id"
  label="Respondent ID"
  value={respondentId}
  setValue={(newValue) => (respondentId = newValue)}
/>
