<script lang="ts">
  import Title from "../../../Title.svelte";
  import Panel from "../../../dashboard/Panel/Panel.svelte";
  import Button from "../../../inputs/Button/Button.svelte";
  import FileInput from "../../../inputs/FileInput/FileInput.svelte";
  import StepTitle from "../../../surveyImport/StepTitle/StepTitle.svelte";
  import MaterialIcon from "../../../MaterialIcon.svelte";
  import Check from "../../../svg/material/Check.svelte";
  import CheckCircle from "../../../svg/material/CheckCircle.svelte";
  import Upload from "../../../svg/material/Upload.svelte";
  import Warning from "../../../svg/material/Warning.svelte";

  import {
    buildConsultationDeepValidationQuery,
    buildConsultationUploadQuery
  } from "../../../../global/queries/consultations/queries";
  import { Routes } from "../../../../global/routes";

  interface Props {
    consultationId: string;
  };

  let {
    consultationId,
  }: Props = $props();

  let deepValidation = $derived(
    buildConsultationDeepValidationQuery(consultationId),
  );

  let upload = $derived(
    buildConsultationUploadQuery(consultationId),
  );

  let fileUploadedForValidation = $derived(deepValidation.query.data);

  const MB_200 = 209715200;

  let fileChosen: null | File = $state(null);

  function resetFileChosen() {
    fileUploadedForValidation = null;
    fileChosen = null;
  }
</script>

<section>
  <StepTitle stepNo={3} title="Upload your file" Icon={Upload} />

  <p class="text-neutral-500 mt-4 mb-6">
    Provided data is in the correct format, Consult uploads it into the app.
  </p>
</section>

<section>
  <Panel>
    {#if !fileUploadedForValidation}
      <FileInput
        id="file-upload"
        title="Drop your file here"
        subtitle=".xlsx or .csv, up to 200MB"
        accept=".csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        multiple={false}
        maxSize={MB_200}
        confirmHint="Checking sends the file to Consult. Nothing is added to the consultation yet."
        confirmButtonText="Check the file"
        onConfirm={async (files: File[]) => {
          // There should only be 1 file selected as multiple is set to false
          // but in case there are more, use only the first one
          const file = files[0];
          fileChosen = file;

          const formData = new FormData();
          formData.append("file", file);

          let response;
          try {
            response = await deepValidation.fetch({ body: formData });
          } catch (e) {
            console.error(e);
            return;
          }

          console.log("r", response)
        }}
      />
    {:else}
      {#if !deepValidation.query.data?.valid}
        <div class="p-2">
          <div class="flex items-center gap-2">
            <MaterialIcon color="fill-red-800" size="1.5rem">
              <Warning />
            </MaterialIcon>
            <Title level={2}>
              <span class="text-md">This file is not valid</span>
            </Title>
          </div>

          <div>
            <p class="text-neutral-500 text-md my-4">
              The file {(fileChosen! as File).name} does not meet the requirements.
            </p>

            {#if deepValidation.query.data?.errors}
              <ul class="list-disc">
                {#each deepValidation.query.data?.errors as error, i (i)}
                  <li class="text-red-500 text-sm ml-8 mt-4 mb-8">
                    {#if error.cell}
                      <span>Cell {error.cell}:</span>
                    {/if}

                    {error.message}
                  </li>
                {/each}
              </ul>
            {/if}
          </div>

          <div>
            <Button
              variant="primary"
              handleClick={resetFileChosen}
            >
              Choose a different file
            </Button>
            <Button
              variant="outline"
              href="/"
            >
              Back to the checklist
            </Button>
          </div>
        </div>
      {:else}
        {@const fileName = (fileChosen! as File).name}

        <div class="p-2">
          <div class="flex items-center gap-2">
            <MaterialIcon color="fill-secondary" size="1.5rem">
              <CheckCircle />
            </MaterialIcon>
            <Title level={2}>
              <span class="text-md">{fileName} passed the checks</span>
            </Title>
          </div>

          <p class="text-neutral-500 text-md my-4">
            The file can be read and is laid out for Consult.
          </p>

          <div class="flex gap-2 items-center my-8">
            <MaterialIcon color="fill-secondary" size="1.5rem">
              <Check />
            </MaterialIcon>

            <p>The file opens and every row can be read</p>
          </div>

          <div class="flex gap-12 items-center border-t border-b py-4">
            {#snippet infoItem(number: number, text: string)}
              <p class="flex flex-col">
                <span class="text-2xl font-[500]">{number || 0}</span>
                <span class="text-sm text-neutral-500">{text}</span>
              </p>
            {/snippet}

            {@render infoItem(deepValidation.query.data?.question_count, "questions found")}
            {@render infoItem(deepValidation.query.data?.response_count, "responses found")}
            {@render infoItem(deepValidation.query.data?.blank_cell_count, "cells left blank")}
          </div>

          <div>
            <p class="text-neutral-800 my-4">
              Uploading adds the responses to Consult. This can take a few hours. You can leave once the file is uploaded. The consultation page shows when the responses are added.
            </p>

            <p class="text-neutral-500">
              One file per consultation. It cannot be replaced after it is uploaded.
            </p>

            <div class="my-4">
              <Button
                variant="text"
                noPadding={true}
                handleClick={resetFileChosen}
              >
                Choose a different file
              </Button>
            </div>
          </div>

          <Panel bg={true} border={true}>
            <p class="text-neutral-500">
              The content of the responses has not been read. Whether personal information has been removed, and whether the wording is right, is still yours to confirm. You'll see every question once the responses are added.
            </p>
          </Panel>

          <div class="flex justify-between mt-8">
            <Button
              variant="outline"
              href="/"
            >
              Back
            </Button>
            <Button
              variant="primary"
              href="/"
            >
              Upload Responses
            </Button>
          </div>
        </div>
      {/if}
    {/if}
  </Panel>
</section>
