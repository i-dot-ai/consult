<script>
  import EditUser from "./EditUser.svelte";

  export let userId = "test-user-id";
</script>

<!-- Wrapper for testing component with props -->
<EditUser {userId} />
