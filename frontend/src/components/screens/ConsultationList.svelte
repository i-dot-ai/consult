<script lang="ts">
  import { onMount } from "svelte";
  import { slide } from "svelte/transition";

  import Title from "../Title.svelte";
  import Link from "../Link.svelte";

  import type { Consultation } from "../../global/types.ts";
  import {
    Routes,
    getConsultationDetailUrl,
    getConsultationEvalUrl,
  } from "../../global/routes.ts";

  let consultations: Consultation[] = [];
  let loading: boolean = true;
  let dashboardPermitted: boolean = false;

  onMount(async () => {
    loading = true;
    const response = await fetch(Routes.ApiConsultations);
    const consultationData = await response.json();
    consultations = consultationData.results;
    loading = false;
  });

  onMount(async () => {
    loading = true;
    const response = await fetch(Routes.ApiUser);
    const userData = await response.json();
    dashboardPermitted = userData.has_dashboard_access;
    loading = false;
  });
</script>

<section class="mt-4">
  {#if loading}
    <p transition:slide>Loading consultations...</p>
  {:else}
    <ul>
      {#each consultations as consultation}
        <li>
          <Title level={2} text={consultation.title} />

          <div class="flex gap-2">
            <Link href={getConsultationEvalUrl(consultation.id)}>
              View Evaluation
            </Link>
            {#if dashboardPermitted}
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
