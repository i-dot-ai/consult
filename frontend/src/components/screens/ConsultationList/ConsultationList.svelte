<script lang="ts">
  import { slide } from "svelte/transition";

  import Title from "../../Title.svelte";
  import Link from "../../Link.svelte";
  import LoadingMessage from "../../LoadingMessage/LoadingMessage.svelte";

  import {
    getConsultationDetailUrl,
    getConsultationEvalUrl,
    getThemeSignOffUrl,
  } from "../../../global/routes.ts";
  import { buildConsultationsGetQuery } from "../../../global/queries/consultations/queries.ts";
  import Alert from "../../Alert.svelte";

  const consultations = buildConsultationsGetQuery();
</script>

<section class="mt-4">
  {#if consultations.query.error}
    <Alert>
      <p>{consultations.query.error?.message || "An error happened"}</p>
    </Alert>
  {:else if consultations.query.isPending}
    <p transition:slide>
      <LoadingMessage message="Loading consultations..." />
    </p>
  {:else if consultations.query?.data?.results?.length === 0}
    No consultations available
  {:else}
    <ul>
      {#each consultations.query.data?.results as consultation (consultation.id)}
        <li>
          <Title level={2} text={consultation.title} />

          <div class="flex flex-wrap gap-4">
            <Link href={getConsultationEvalUrl(consultation.id)}>
              View Evaluation
            </Link>
            <Link href={getThemeSignOffUrl(consultation.id)}>
              Theme Sign Off
            </Link>
            <Link href={getConsultationDetailUrl(consultation.id)}>
              View Dashboard
            </Link>
          </div>
        </li>
      {/each}
    </ul>
  {/if}
</section>
