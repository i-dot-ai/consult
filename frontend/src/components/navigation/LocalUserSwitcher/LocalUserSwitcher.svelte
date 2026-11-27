<script lang="ts">
  import { onMount } from "svelte";

  import { LOCAL_USERS } from "../../../global/localUsers";

  const USERS = [
    { email: LOCAL_USERS.ADMIN.EMAIL, label: "Admin" },
    { email: LOCAL_USERS.POLICY.EMAIL, label: "Policy user" },
  ];

  let currentEmail = $state(LOCAL_USERS.ADMIN.EMAIL);

  onMount(() => {
    const match = document.cookie.match(/(?:^|;\s*)dev_email=([^;]*)/);
    if (match) currentEmail = decodeURIComponent(match[1]);
  });

  const switchUser = (email: string) => {
    document.cookie = `dev_email=${email}; path=/; SameSite=Strict`;
    currentEmail = email;
    window.location.reload();
  };
</script>

<div
  class="flex items-center gap-1 rounded-sm border border-warning bg-warning-light-95 px-2 py-1 text-xs"
>
  <span class="font-medium text-warning-dark-50">Dev:</span>
  {#each USERS as user (user.email)}
    <button
      class="rounded cursor-pointer px-1.5 py-0.5 transition-colors {currentEmail ===
      user.email
        ? 'bg-warning font-medium text-white'
        : 'text-warning-dark-25 hover:bg-warning-light-95'}"
      onclick={() => switchUser(user.email)}
    >
      {user.label}
    </button>
  {/each}
</div>
