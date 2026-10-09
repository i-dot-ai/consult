<script lang="ts">
  import { buildConsultationDeleteQuery } from "../../global/queries/consultations/queries";
  import type { Consultation } from "../../global/types";
  import Panel from "../dashboard/Panel/Panel.svelte";
  import Modal from "../Modal/Modal.svelte";
  import Warning from "../svg/material/Warning.svelte";

  interface Props {
    consultation?: Consultation;
    onClose?: () => void;
    onError?: (consultation: Consultation) => void;
    onSuccess?: (consultation: Consultation) => void;
  }

  let { consultation, onClose, onError, onSuccess }: Props = $props();

  let isOpen = $derived(Boolean(consultation));

  const consultationDelete = $derived(
    buildConsultationDeleteQuery(consultation?.id || ""),
  );
</script>

<Modal
  variant="warning"
  open={isOpen}
  setOpen={(newOpen: boolean) => {
    if (newOpen === false) {
      isOpen = false;

      if (onClose) {
        onClose();
      }
    }
  }}
  title="Delete consultation"
  Icon={Warning}
  canCancel={true}
  confirmText="Delete consultation"
  handleConfirm={async () => {
    if (!consultation) {
      return;
    }

    try {
      await consultationDelete.fetch({});

      if (onSuccess) {
        onSuccess(consultation);
      }
    } catch {
      console.error(consultationDelete.query?.error?.message);

      if (onError) {
        onError(consultation);
      }
    }
  }}
>
  <p>
    Deleting removes the responses, the themes and the analysis. This cannot be
    undone.

    <Panel variant="default">
      {consultation?.title || "Consultation not selected"}
    </Panel>
  </p>
</Modal>
