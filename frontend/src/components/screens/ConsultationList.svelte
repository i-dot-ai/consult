<script lang="ts">
  import { slide } from "svelte/transition";

  import Title from "../Title.svelte";
  import Link from "../Link.svelte";
  import LoadingMessage from "../LoadingMessage/LoadingMessage.svelte";

  import type { ConsultationsResponse, UserResponse } from "../../global/types.ts";
  import {
    Routes,
    getConsultationDetailUrl,
    getConsultationEvalUrl,
    getThemeSignOffUrl,
  } from "../../global/routes.ts";
  import { buildQuery } from "../../global/queries.ts";

  const consultationsQuery = buildQuery<ConsultationsResponse>(
    `${Routes.ApiConsultations}?scope=assigned`,
    { key: ["consultations"] },
  );
  const userQuery = buildQuery<UserResponse>(
    Routes.ApiUser,
    { key: ["user"] },
  );
</script>

<section class="mt-4">
  {#if consultationsQuery.isPending || userQuery.isPending}
    <p transition:slide>
      <LoadingMessage message="Loading consultations..." />
    </p>
  {:else if consultationsQuery.isError}
    <p>{consultationsQuery.error}</p>
  {:else}
    <ul>
      {#each consultationsQuery.data?.results as consultation (consultation.id)}
        <li>
          <Title level={2} text={consultation.title} />

          <div class="flex flex-wrap gap-4">
            <Link href={getConsultationEvalUrl(consultation.id)}>
              View Evaluation
            </Link>
            <Link href={getThemeSignOffUrl(consultation.id)}>
              Theme Sign Off
            </Link>
            {#if userQuery.data?.has_dashboard_access}
              <Link href={getConsultationDetailUrl(consultation.id)}>
                View Dashboard
              </Link>
            {/if}
          </div>
        </li>
      {/each}
    </ul>
  {/if}
</section>
