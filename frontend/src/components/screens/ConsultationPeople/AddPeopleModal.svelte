<script lang="ts">
  import Alert from "../../Alert/Alert.svelte";
  import Textarea from "../../inputs/Textarea/Textarea.svelte";
  import Modal from "../../Modal/Modal.svelte";
  import ErrorIcon from "../../svg/material/Error.svelte";
  import { parseEmails } from "../AddUserForm/parseEmails";
  import { EMAIL_PATTERN, type AddResult } from "./people";

  interface Props {
    consultationTitle: string;
    existingEmails: string[];
    onClose: () => void;
    onAdd: (
      newEmails: string[],
      alreadyOnEmails: string[],
    ) => Promise<AddResult>;
  }

  let { consultationTitle, existingEmails, onClose, onAdd }: Props = $props();

  const FIELD_ID = "add-people-emails";

  let emailsInput = $state("");
  let error = $state("");
  let saving = $state(false);

  async function submit() {
    const emails = [
      ...new Set(parseEmails(emailsInput).map((email) => email.toLowerCase())),
    ];
    if (emails.length === 0) {
      error = "Enter at least one email address";
      return;
    }
    const malformed = emails.filter((email) => !EMAIL_PATTERN.test(email));
    if (malformed.length > 0) {
      error = `Enter email addresses in the right format, like name@example.gov.uk. Check ${malformed.join(", ")}`;
      return;
    }
    const existingSet = new Set(
      existingEmails.map((email) => email.toLowerCase()),
    );
    const alreadyOnEmails = emails.filter((email) => existingSet.has(email));
    const newEmails = emails.filter((email) => !existingSet.has(email));
    error = "";
    saving = true;
    try {
      const result = await onAdd(newEmails, alreadyOnEmails);
      if (result.outcome === "failed") {
        error = "The people were not added. Try again.";
      }
    } finally {
      saving = false;
    }
  }
</script>

<Modal
  open={true}
  compact={true}
  title="Add people"
  confirmText="Add people"
  confirmDisabled={saving}
  setOpen={(next) => {
    if (!next) {
      onClose();
    }
  }}
  handleConfirm={submit}
>
  <p class="text-sm text-neutral-500">
    They can see {consultationTitle} and work on it.
  </p>

  {#if error}
    <div role="alert">
      <Alert variant="error" Icon={ErrorIcon}>
        <p class="font-bold">There is a problem</p>
        <p class="mt-1">
          <a class="underline" href={`#${FIELD_ID}`}>{error}</a>
        </p>
      </Alert>
    </div>
  {/if}

  <div class="emails-field">
    <Textarea
      id={FIELD_ID}
      label="Email addresses"
      hint="Enter one or more, separated by commas, spaces or new lines."
      errorMessage={error}
      rows={4}
      value={emailsInput}
      setValue={(value) => (emailsInput = value)}
      disabled={saving}
    />
  </div>
</Modal>

<style>
  @reference "../../../styles/global.css";

  .emails-field :global(label) {
    @apply text-sm font-medium text-neutral-900;
  }
</style>
