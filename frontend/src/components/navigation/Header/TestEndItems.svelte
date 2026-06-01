<script lang="ts">
  import ProfileButton from "../ProfileButton/ProfileButton.svelte";
  const isSignedIn = $state(true);
</script>

<div class="relative">
  <ProfileButton {isSignedIn} />
</div>
