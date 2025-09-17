<script lang="ts">
    import TextInput from "../../inputs/TextInput/TextInput.svelte";
    import RespondentAnswer from "./RespondentAnswer.svelte";


    let questionTitle = $state("Do you agree with the proposal to align the flavour categories of chocolate bars as outlined in the draft guidelines of the Chocolate Bar Regulation for the United Kingdom?");
    let questionNumber = $state(1);
    let answerText = $state("I agree in principle, but I think the guidelines should include a provision for periodic review to adapt to market changes.");
    let themes = $state([ "Innovation", "Standardized framework" ]);
</script>

<RespondentAnswer
    questionTitle={questionTitle}
    questionNumber={questionNumber}
    answerText={answerText}
    themes={themes}
/>

<hr class="my-8" />

<TextInput
    id="input-question-title"
    label="Question Title"
    value={questionTitle}
    setValue={(newValue) => questionTitle = newValue}
/>

<TextInput
    id="input-question-number"
    label="Question Number"
    value={questionNumber.toString()}
    setValue={(newValue) => questionNumber = parseInt(newValue)}
/>

<TextInput
    id="input-answer-text"
    label="Answer Text"
    value={answerText}
    setValue={(newValue) => answerText = newValue}
/>

<TextInput
    id="input-themes-all"
    label="Themes"
    value={`[ "Innovation", "Standardized framework" ]`}
    setValue={(newValue) => {
        try {
            themes = JSON.parse(newValue);
        } catch {}
    }}
/>