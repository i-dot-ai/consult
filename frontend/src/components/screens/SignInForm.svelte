<script lang="ts">
  import clsx from "clsx";

  import { slide } from "svelte/transition";

  import { Routes } from "../../global/routes";

  import TextInput from "../inputs/TextInput/TextInput.svelte";
  import Link from "../Link.svelte";
  import Button from "../inputs/Button/Button.svelte";

  const INVALID_EMAIL_MSG = "Please enter a valid email";

  let email: string = "";
  let error: string = "";
  let sending: boolean = false;
  let success: boolean = false;

  const setEmail = (newValue: string) => {
    email = newValue;

    error = email && !email.includes("@") ? INVALID_EMAIL_MSG : "";
  };

  const handleSubmit = async () => {
    error = "";
    success = false;

    if (!email || !email.includes("@")) {
      error = INVALID_EMAIL_MSG;
      return;
    }

    sending = true;

    try {
      const response = await fetch(Routes.ApiAstroSignIn, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email: email }),
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }

      success = true;
      email = "";
    } catch (err: any) {
      error = err.message;
    } finally {
      sending = false;
    }
  };
</script>

<form
  class={clsx(["flex", "flex-col", "gap-4"])}
  on:submit|preventDefault={handleSubmit}
>
  {#if error}
    <small class="text-sm text-red-500" transition:slide={{ duration: 300 }}>
      {error}
    </small>
  {/if}

  {#if success}
    <small class="text-sm text-gray-500" transition:slide={{ duration: 300 }}>
      Link sent. If you have access to Consult check your inbox for an email. If
      you don't have access or don't receive the email please contact
      <Link
        href="mailto:i-dot-ai-enquiries@cabinetoffice.gov.uk"
        title="Email to enquiries"
        ariaLabel="Send email to enquiries"
      >
        i-dot-ai-enquiries@cabinetoffice.gov.uk
      </Link>.
    </small>
  {/if}

  <div class="flex flex-wrap justify-start items-center gap-4">
    <div class="grow max-w-[30ch]">
      <TextInput
        id={"email-input"}
        label={"Email address"}
        hideLabel={true}
        placeholder={"Your email"}
        value={email}
        setValue={setEmail}
      />
    </div>

    <Button variant="primary" handleClick={handleSubmit} disabled={sending}>
      {sending ? "Sending..." : "Continue"}
    </Button>
  </div>
</form>
