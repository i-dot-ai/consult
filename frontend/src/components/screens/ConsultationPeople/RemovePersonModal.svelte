<script lang="ts">
  import Modal from "../../Modal/Modal.svelte";

  import type { ConsultationV2User } from "../../../global/queries/consultations/types";

  interface Props {
    person: ConsultationV2User;
    consultationTitle: string;
    onClose: () => void;
    onConfirm: (person: ConsultationV2User) => Promise<void>;
  }

  let { person, consultationTitle, onClose, onConfirm }: Props = $props();

  let saving = $state(false);

  async function confirm() {
    saving = true;
    try {
      await onConfirm(person);
    } finally {
      saving = false;
    }
  }
</script>

<Modal
  open={true}
  compact={true}
  variant="warning"
  title="Remove from consultation"
  confirmText="Remove"
  confirmDisabled={saving}
  setOpen={(next) => {
    if (!next) {
      onClose();
    }
  }}
  handleConfirm={confirm}
>
  <p class="text-sm text-neutral-500">
    {person.email} can no longer see {consultationTitle}. They can be added
    again.
  </p>
</Modal>
