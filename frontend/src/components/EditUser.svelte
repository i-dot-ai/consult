<script lang="ts">
  import { createFetchStore } from "../global/stores.ts";
  import Switch from "./inputs/Switch/Switch.svelte";
  
  interface Props {
    userId: string;
    isStaff?: boolean;
    hasDashboardAccess?: boolean;
    resetData: () => void;
  }
  
  let { 
    userId, 
    isStaff, 
    hasDashboardAccess, 
    resetData 
  }: Props = $props();


  const {
    load: loadUser,
    loading: isLoadingUser,
    data: userData,
  } = createFetchStore();

  
  // Load user data initially
  $effect(() => {
    loadUser(`/api/users/${userId}/`);
  });
  
  // Use live user data if available, otherwise fall back to props
  let currentIsStaff = $derived($userData?.is_staff ?? isStaff);
  let currentHasDashboardAccess = $derived($userData?.has_dashboard_access ?? hasDashboardAccess);
  
  // State for update errors
  let updateError = $state<string | null>(null);
  
  async function updateUserField(field: string, value: boolean, currentValue: boolean) {
    // Only update if the value is actually different from current server state
    if (value === currentValue) return;
    
    try {
      const response = await fetch(`/api/users/${userId}/`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ [field]: value }),
      });
      
      if (response.status === 400) {
        const errorData = await response.json();
        updateError = errorData[field]?.[0] || "Update failed";
        console.log('400 error details:', errorData);
        return;
      }
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      // Success - clear any previous errors
      updateError = null;
      console.log('Update successful');
      
    } catch (err) {
      console.error('Error updating user:', err);
    }
  }
  
  const updateIsStaff = (value: boolean) => updateUserField('is_staff', value, currentIsStaff);
  const updateHasDashboardAccess = (value: boolean) => updateUserField('has_dashboard_access', value, currentHasDashboardAccess);
</script>

<div class="mb-8">
  {#if $isLoadingUser}
    <div class="text-sm text-gray-600">Loading user data...</div>
  {:else if $userData}
    <!-- User Details -->
    <div class="mb-8">
      <h1 class="text-2xl font-bold mb-4">{$userData.email}</h1>
      <table class="w-full border-collapse">
        <tbody>
          <tr class="border-b">
            <th class="text-left py-3 pr-4 font-semibold">Created at</th>
            <td class="py-3">{new Date($userData.created_at).toLocaleDateString()}</td>
          </tr>
        </tbody>
      </table>
    </div>

    {#if updateError}
      <div class="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded mb-6">
        {updateError}
      </div>
    {/if}

    <div class="space-y-6 max-w-md">
      <div class="space-y-4">
        <div class="flex items-center justify-between">
          <label for="is_staff" class="text-sm font-medium">
            Can access support console
          </label>
          <Switch 
            id="is_staff"
            label=""
            hideLabel={true}
            value={currentIsStaff}
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
            value={currentHasDashboardAccess}
            handleChange={(value) => updateHasDashboardAccess(value)}
          />
        </div>
      </div>
      
      {#if $isLoadingUser}
        <div class="text-sm text-gray-600">
          Updating permissions...
        </div>
      {/if}
    </div>
  {/if}
</div>