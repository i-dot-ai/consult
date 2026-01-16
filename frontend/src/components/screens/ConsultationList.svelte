<script lang="ts">
  import { onMount } from "svelte";

  import Alert from "../Alert.svelte";
  import Title from "../Title.svelte";
  import Link from "../Link.svelte";
  import LoadingMessage from "../LoadingMessage/LoadingMessage.svelte";

  import type { ApiError, ConsultationsResponse, UserResponse } from "../../global/types.ts";
  import {
    Routes,
    getConsultationDetailUrl,
    getConsultationEvalUrl,
    getThemeSignOffUrl,
  } from "../../global/routes.ts";
  import { createQueryStore } from "../../global/stores.ts";

  let consultationsStore = createQueryStore<ConsultationsResponse>(
    `${Routes.ApiConsultations}?scope=assigned`
  );
  let userStore = createQueryStore<UserResponse>(Routes.ApiUser);

  onMount(async () => {
    await $consultationsStore.fetch();
    await $userStore.fetch();
  });

  let dashboardPermitted = $derived($userStore?.data?.has_dashboard_access);
</script>

<section class="mt-4">
  {#if $consultationsStore.isLoading || $userStore.isLoading }
    <p>
      <LoadingMessage message="Loading consultations..." />
    </p>
  {:else if $consultationsStore.error || $userStore.error }
    <Alert>
      {($consultationsStore.error as ApiError).detail || ($userStore.error as ApiError).detail}
    </Alert>
  {:else}
    <ul>
      {#each $consultationsStore.data?.results as consultation (consultation.id)}
        <li>
          <Title level={2} text={consultation.title} />

          <div class="flex flex-wrap gap-4">
            <Link href={getConsultationEvalUrl(consultation.id)}>
              View Evaluation
            </Link>
            <Link href={getThemeSignOffUrl(consultation.id)}>
              Theme Sign Off
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
