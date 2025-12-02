<script lang="ts">
  import { onMount } from "svelte";
  import { createFetchStore } from "../../../global/stores.ts";
  import Switch from "../../inputs/Switch/Switch.svelte";

  export interface Props {
    userId: string;
  }

  let { userId }: Props = $props();

  const {
    load: loadUser,
    loading: isLoadingUser,
    data: userData,
  } = createFetchStore();

  const {
    load: updateUser,
    data: updateUserData,
    error: updateUserError,
  } = createFetchStore();

  // Load user data initially
  onMount(() => {
    loadUser(`/api/users/${userId}/`);
  });

  async function updateIsStaff(value: boolean) {
    if (value === $userData?.is_staff) return; // Don't update if value hasn't changed

    await updateUser(`/api/users/${userId}/`, "PATCH", { is_staff: value });

    loadUser(`/api/users/${userId}/`);
  }

  async function updateHasDashboardAccess(value: boolean) {
    if (value === $userData?.has_dashboard_access) return; // Don't update if value hasn't changed

    await updateUser(`/api/users/${userId}/`, "PATCH", {
      has_dashboard_access: value,
    });

    loadUser(`/api/users/${userId}/`);
  }
</script>

<div class="mb-8">
  {#if $isLoadingUser}
    <div class="text-sm text-gray-600">Loading user data...</div>
  {:else if $userData}
    <!-- User Details -->
    <div class="mb-8">
      <h1 class="mb-4 text-2xl font-bold">{$userData.email}</h1>
      <table class="w-full border-collapse">
        <tbody>
          <tr class="border-b">
            <th class="py-3 pr-4 text-left font-semibold">Created at</th>
            <td class="py-3"
              >{new Date($userData.created_at).toLocaleDateString()}</td
            >
          </tr>
        </tbody>
      </table>
    </div>

    {#if $updateUserError}
      <div
        class="mb-6 rounded border border-red-200 bg-red-50 px-4 py-3 text-red-800"
      >
        {$updateUserData?.is_staff[0] || "failed to update user"}
      </div>
    {/if}

    <div class="max-w-md space-y-6">
      <div class="space-y-4">
        <div class="flex items-center justify-between">
          <label for="is_staff" class="text-sm font-medium">
            Can access support console
          </label>
          <Switch
            id="is_staff"
            label=""
            hideLabel={true}
            value={$userData.is_staff}
            handleChange={(value) => updateIsStaff(value)}
          />
        </div>

        <div class="flex items-center justify-between">
          <label for="has_dashboard_access" class="text-sm font-medium">
            Can access dashboards
          </label>
          <Switch
            id="has_dashboard_access"
            label=""
            hideLabel={true}
            value={$userData.has_dashboard_access}
            handleChange={(value) => updateHasDashboardAccess(value)}
          />
        </div>
      </div>

      {#if $isLoadingUser}
        <div class="text-sm text-gray-600">Updating permissions...</div>
      {/if}
    </div>
  {/if}
</div>
