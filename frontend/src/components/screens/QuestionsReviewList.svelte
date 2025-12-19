<script lang="ts">
  import type { Question, ShowNextResponseResult } from "../../global/types";
  import { getApiShowNextResponse, getResponseDetailUrl } from "../../global/routes";
  import MaterialIcon from "../MaterialIcon.svelte";
  import Visibility from "../svg/material/Visibility.svelte";
  import Button from "../inputs/Button/Button.svelte";
  
  export let consultationId: string;
  export let questions: Question[] = [];
  
  let loadingStates: { [key: string]: boolean } = {};
  let errors: { [key: string]: string | null } = {};

  const handleShowNext = async (questionId: string) => {
    loadingStates[questionId] = true;
    errors[questionId] = null;
    
    try {
      const response = await fetch(
        getApiShowNextResponse(consultationId, questionId),
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result: ShowNextResponseResult = await response.json();

      if (result.next_response) {
        // Redirect to the next response
        window.location.href = getResponseDetailUrl(
          result.next_response.consultation_id,
          result.next_response.question_id,
          result.next_response.id,
        );
      } else {
        // No more responses to review
        if (!result.has_free_text) {
          errors[questionId] = "This question does not have free text responses.";
        } else {
          errors[questionId] = "No more responses to review.";
        }
      }
    } catch (err) {
      console.error("Error fetching next response:", err);
      errors[questionId] = "Failed to fetch next response. Please try again.";
    } finally {
      loadingStates[questionId] = false;
    }
  };
</script>

<form class="pt-4">
  {#each questions as question (question.id)}
    {#if errors[question.id!]}
      <div class="pt-1 shrink grow text-sm text-red-600">
        {errors[question.id!]}
      </div>
    {/if}
    <div class="mx-0 mt-0 flex items-center justify-between pb-4">
      <p class="m-0 shrink grow basis-0">{question.question_text}</p>
      <p class="m-0 min-w-[15ch] px-4 py-0 text-center">
        {Math.round((question.proportion_of_audited_answers || 0) * 100)}%
        reviewed
      </p>
      <div class="flex flex-col items-end">
        <Button
          type="button"
          variant="outline"
          handleClick={() => handleShowNext(question.id!)}
          disabled={loadingStates[question.id!] || false}
        >
          <MaterialIcon color="fill-neutral-500" size="1rem">
            <Visibility />
          </MaterialIcon>
          {#if loadingStates[question.id!]}
            Loading...
          {:else}
            Show next
          {/if}
        </Button>
      </div>
    </div>
  {/each}
</form>