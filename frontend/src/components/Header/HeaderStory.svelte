<script lang="ts">
  import Title from "../Title.svelte";
  import Header from "./Header.svelte";
</script>

<div>
  <Title level={2} text="Is Signed In" />
  <Header isSignedIn={true} />
</div>

<div>
  <Title level={2} text="Not Signed In" />
  <Header isSignedIn={false} />
</div>
