<script lang="ts">
  import clsx from "clsx";

  import { slide } from "svelte/transition";

  import {
    getApiQuestionUrl,
    getSupportConsultationDetails,
  } from "../../global/routes";

  import Button from "../inputs/Button/Button.svelte";
  import Text from "../Text/Text.svelte";
  import InsetText from "../InsetText/InsetText.svelte";
  import type { ConsultationResponse, Question } from "../../global/types";

  let sending: boolean = false;
  let errors: Record<string, string> = {};

  export let consultation: ConsultationResponse;
  export let question: Question;

  const handleSubmit = async () => {
    errors = {};
    sending = true;
    try {
      const response = await fetch(
        getApiQuestionUrl(consultation.id, question.id!),
        {
          method: "DELETE",
          headers: {
            "Content-Type": "application/json",
          },
        },
      );

      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      window.location.href = getSupportConsultationDetails(consultation.id);
    } catch (err: unknown) {
      errors["general"] =
        err instanceof Error ? err.message : "An unknown error occurred";
    } finally {
      sending = false;
    }
  };

  const handleCancel = () => {
    window.location.href = getSupportConsultationDetails(consultation.id);
  };
</script>

<form class={clsx(["flex", "flex-col", "gap-4"])}>
  {#if "general" in errors}
    <small class="text-sm text-red-500" transition:slide={{ duration: 300 }}>
      {errors.general}
    </small>
  {/if}

  <Text>
    This question is part of the consultation with title: <strong
      >{consultation.title}</strong
    >
  </Text>

  <Text>Are you sure you want to delete the following question?</Text>

  <InsetText>
    {#snippet children()}
      <Text>{question.question_text}</Text>
    {/snippet}
  </InsetText>

  <div class="flex gap-4">
    <Button
      type="button"
      variant="primary"
      handleClick={handleSubmit}
      disabled={sending}
    >
      {sending ? "Deleting..." : "Yes, delete it"}
    </Button>

    <Button
      type="button"
      variant="outline"
      handleClick={handleCancel}
      disabled={sending}
    >
      No, go back
    </Button>
  </div>
</form>
