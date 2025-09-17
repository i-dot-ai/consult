<script lang="ts">
    import TextInput from "../../inputs/TextInput/TextInput.svelte";
    import RespondentSidebar from "./RespondentSidebar.svelte";


    let respondentType: string = $state("Test Institution Public Sector");
    let geographicLocation: string = $state("Northern Ireland");
    let selfReportedDisability: string = $state("Yes");
    let sector: string = $state("Non-profit");
    let stakeholderName: string = $state("Test stakeholder");
    let questionsAnswered: number = $state(8);
    let totalQuestions: number = $state(10);
</script>

<RespondentSidebar
    {respondentType}
    {geographicLocation}
    {selfReportedDisability}
    {sector}
    {stakeholderName}
    {questionsAnswered}
    {totalQuestions}
    updateStakeholderName={(newStakeholderName) => stakeholderName = newStakeholderName}
/>

<hr class="my-8" />

<TextInput
    id="input-respondent-type"
    label="Respondent Type"
    value={respondentType}
    setValue={(newValue) => respondentType = newValue}
/>

<TextInput
    id="input-geographic-location"
    label="Geographic Location"
    value={geographicLocation}
    setValue={(newValue) => geographicLocation = newValue}
/>

<TextInput
    id="input-self-reported-disability"
    label="Self-Reported Disability"
    value={selfReportedDisability}
    setValue={(newValue) => selfReportedDisability = newValue}
/>

<TextInput
    id="input-sector"
    label="Sector"
    value={sector}
    setValue={(newValue) => sector = newValue}
/>

<TextInput
    id="input-stakeholderName"
    label="Stakeholder Name"
    value={stakeholderName}
    setValue={(newValue) => stakeholderName = newValue}
/>

<TextInput
    id="input-questions-answered"
    label="Questions Answered"
    value={questionsAnswered.toString()}
    setValue={(newValue) => questionsAnswered = parseInt(newValue)}
/>

<TextInput
    id="input-total-questions"
    label="Total Questions"
    value={totalQuestions.toString()}
    setValue={(newValue) => totalQuestions = parseInt(newValue)}
/>