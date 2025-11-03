<script lang="ts">
  import { onMount } from "svelte"
  import { createFetchStore } from "../../global/stores.ts";
  import type { Writable } from "svelte/store";
  import type {Question }  from "../../global/types.ts";
  import Button from "../inputs/Button/Button.svelte";
  import TextInput from "../inputs/TextInput/TextInput.svelte";


  export interface Props {
    consultationId: string,
  }
  
  let { 
    consultationId,
  }: Props = $props();

  interface questionResponse {
    results: Question[]
  }


  const {
    load: loadQuestions,
    loading: isLoadingQuestions,
    data: questionsData,
    error: questionsError,
  } : {
    load: Function;
    loading: Writable<boolean>;
    data: Writable<questionResponse>;
    error: Writable<string>;
  } = createFetchStore();

  // State for tracking export status of each question
  let exportStatus = $state<Record<string, 'idle' | 'exporting' | 'success' | 'error'>>({});
  
  // S3 key input
  let s3Key = $state('exports');

  onMount(() => {
    loadQuestions(`/api/consultations/${consultationId}/questions`);
  });



  // Helper function to get status for a question
  function getStatus(questionId: string) {
    return exportStatus[questionId] || 'idle';
  }

  async function exportQuestion(questionId: string) {
    exportStatus[questionId] = 'exporting';
    
    try {
      const response = await fetch(`/api/consultations/${consultationId}/questions/${questionId}/export/`, {
        method: 'PATCH',
        body: JSON.stringify({s3_key: s3Key}),
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      exportStatus[questionId] = response.ok ? 'success' : 'error';
    } catch (error) {
      exportStatus[questionId] = 'error';
    }
  }

</script>

{#if $questionsData?.results}
  <div class="mb-6">
    <label for="s3-key" class="block text-sm font-medium text-gray-700 mb-2">
      S3 Export Directory:
    </label>
    <TextInput
      id="s3-key"
      bind:value={s3Key}
      placeholder="exports"
    />
    <p class="text-sm text-gray-600 mt-1">
      Files will be saved to: s3://bucket/{s3Key}/[timestamp]_question_[number]_theme_changes.csv
    </p>
  </div>
  
  <ul class="list-none p-0 m-0 space-y-4">
    {#each $questionsData.results as question}
      {@const status = getStatus(question.id || '')}
      <li class="border border-gray-200 p-4 rounded">
        <p class="mb-2"><strong>Question {question.number}</strong> - {question.question_text}</p>
        <div class="flex gap-2 items-center mt-2">
          <Button
            variant={status === 'success' ? 'approve' : 'primary'}
            disabled={status === 'exporting'}
            handleClick={() => exportQuestion(question.id || '')}
          >
            {#if status === 'exporting'}
              Exporting...
            {:else if status === 'success'}
              ✓ Exported
            {:else if status === 'error'}
              Try Again
            {:else}
              Export
            {/if}
          </Button>
        </div>
        
        {#if status === 'error'}
          <div class="mt-2 p-2 rounded bg-red-100 text-red-800 border border-red-200">
            <span class="text-sm">✗ Export failed. Please try again.</span>
          </div>
        {/if}
      </li>
    {/each}
  </ul>
{:else}
  <p>No questions found.</p>
{/if}
