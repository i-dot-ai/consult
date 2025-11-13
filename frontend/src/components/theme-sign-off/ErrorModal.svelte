<script lang="ts">
  import Modal from "../Modal/Modal.svelte";
  import Warning from "../svg/material/Warning.svelte";

  export type ErrorType =
    | {
        type: "unexpected" | "theme-does-not-exist";
      }
    | {
        type: "edit-conflict" | "remove-conflict";
        lastModifiedBy: string;
        latestVersion: string;
      };
  type ErrorModalProps = ErrorType & {
    onClose: () => void;
  };

  let props: ErrorModalProps = $props();

  let isOpen = $state(true);

  const handleConfirm = () => {
    isOpen = false;
    props.onClose();
  };

  const getModalContent = (props: ErrorModalProps) => {
    switch (props.type) {
      case "theme-does-not-exist":
        return {
          title: "Theme Deselected",
          message:
            "Another user has deselected this theme whilst you were editing it. Your edits will not be saved and the theme is no longer a selected theme.",
          confirmText: "Got it",
          canCancel: false,
        };

      case "edit-conflict":
        return {
          title: "Theme Conflict Detected",
          message: `${props.lastModifiedBy} has edited this theme since you started editing. Please refresh to see the latest version before editing.`,
          confirmText: "Refresh",
          canCancel: true,
        };

      case "remove-conflict":
        return {
          title: "Theme Conflict Detected",
          message: `This theme has been edited by ${props.lastModifiedBy} since you loaded the page. Please refresh to see the latest version before removing.`,
          confirmText: "Refresh",
          canCancel: false,
        };

      default:
        return {
          title: "Unexpected Error",
          message:
            "An unexpected error occurred and your changes have not been saved. Please try again.",
          confirmText: "Got it",
          canCancel: false,
        };
    }
  };

  let content = $derived(getModalContent(props));
</script>

<Modal
  variant="warning"
  open={isOpen}
  setOpen={(newOpen: boolean) => (isOpen = newOpen)}
  title={content.title}
  icon={Warning}
  canCancel={content.canCancel}
  confirmText={content.confirmText}
  {handleConfirm}
>
  <p class="text-sm text-gray-600 mb-4">
    {content.message}
  </p>
</Modal>
