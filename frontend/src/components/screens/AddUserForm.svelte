<script lang="ts">
  import clsx from "clsx";

  import Title from "../Title.svelte";
  import TextInput from "../inputs/TextInput/TextInput.svelte";
  import Button from "../inputs/Button/Button.svelte";

  let email: string = "";
  let errorMessage: string = "";
  let loading: boolean = false;

  const setEmail = (inputtedEmail: string) => {
    email = inputtedEmail;
  };

  const handleSubmit = async () => {
    loading = true;

    try {
      const res = await fetch("/api/users/", {
        method: "POST",
        body: JSON.stringify({ email }),
        headers: { "Content-Type": "application/json" },
      });

      if (res.ok) {
        window.location.href = "/support/users";
      } else {
        const data = await res.json();
        errorMessage = data?.email?.[0] || "something went wrong.";
      }

    } catch (err: any) {
      errorMessage = err.message || "something went wrong.";
    } finally {
      loading = false;
    }
  };
</script>

<Title level={1} text="Add a user" />
<form
  class={clsx([ "max-w-md", "mt-4", "flex", "flex-col", "gap-4"])}
  on:submit|preventDefault={handleSubmit}
>

  <TextInput
    id={"email"}
    label={"Email address"}
    inputType="email"
    value={email}
    setValue={setEmail}
  />

  {#if errorMessage}
    <p class="text-sm text-red-500">{`Error: ${errorMessage}`}</p>
  {/if}

  <div class="flex">
    <Button variant="primary" disabled={loading}>
      Add user
    </Button>
  </div>
</form>
