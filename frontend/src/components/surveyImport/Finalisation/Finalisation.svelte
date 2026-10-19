<script lang="ts">
  import CheckCircle from "../../svg/material/CheckCircle.svelte";
  import Button from "../../inputs/Button/Button.svelte";
  import StepTitle from "../StepTitle/StepTitle.svelte";

  import { getConsultationViewUrl } from "../../../global/routes";

  interface Props {
    consultationId: string;
  }

  let { consultationId }: Props = $props();
</script>

<StepTitle stepNo={6} maxStepNo={6} title="Setup complete" Icon={CheckCircle} />

<p class="mt-3.5 mb-[26px] text-[15px] leading-relaxed text-neutral-500">
  The responses have been uploaded and all questions configured. Consult will
  now find themes across the open question responses.
</p>

<div class="rounded-xl border border-neutral-300 bg-white p-7">
  <p class="text-[15px] leading-relaxed text-neutral-900">
    Finding themes can take more than 20 minutes, but can take longer depending
    on the size of your consultation. You can leave and come back from the
    consultation page at any time. Your consultation status will be updated when
    the themes are ready.
  </p>
</div>

<div class="mt-7 flex justify-end">
  <Button
    size="sm"
    variant="primary"
    href={getConsultationViewUrl(consultationId)}
  >
    Go to consultation page
  </Button>
</div>
