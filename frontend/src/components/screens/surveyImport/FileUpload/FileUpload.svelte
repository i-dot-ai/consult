<script lang="ts">
  import Panel from "../../../dashboard/Panel/Panel.svelte";
  import FileInput from "../../../inputs/FileInput/FileInput.svelte";
  import MaterialIcon from "../../../MaterialIcon.svelte";
  import StepTitle from "../../../surveyImport/StepTitle/StepTitle.svelte";
  import Check from "../../../svg/material/Check.svelte";
  import CheckCircle from "../../../svg/material/CheckCircle.svelte";
  import Upload from "../../../svg/material/Upload.svelte";


  const MB_200 = 209715200;

  let fileChosen: null | File = $state(null);

  function verifyFile(file: File) {
    console.log("verifying:", file);
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
    {#if !fileChosen}
      <FileInput
        id="file-upload"
        title="Drop your file here"
        subtitle=".xlsx or .csv, up to 200MB"
        accept=".csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        multiple={false}
        maxSize={MB_200}
        onConfirm={(files: File[]) => {
          console.log(files);

          files.forEach(file => {
            verifyFile(file);
            fileChosen = file;
          });

        }}
      />
    {/if}

    {#if fileChosen}
      {const file = fileChosen as File}
      <div class="flex gap-2 items-center">
        <MaterialIcon color="fill-secondary">
          <CheckCircle />
        </MaterialIcon>

        {file?.name} is ready
      </div>

      <p class="text-sm text-neutral-500 mt-2">The file can be read and is laid out for Consult.</p>

      <div class="flex gap-2 items-center my-4">
        <MaterialIcon color="fill-secondary">
          <Check />
        </MaterialIcon>

        <p class="text-sm">The file opens and every row can be read</p>
      </div>

      <hr class="my-8" />

      <Panel bg={true}>
        <p class="text-sm text-neutral-500">
          The content of the responses has not been read. Whether personal information has been removed, and whether the wording is right, is still yours to confirm. You'll see every question in the next step.
        </p>
      </Panel>
    {/if}
  </Panel>
</section>