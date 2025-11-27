<script lang="ts">
    import { updateResponseReadStatus } from "../../../global/routes";

  interface Props {
    responseId: string;
    consultationId: string;
    children?: any;
  }

  let { consultationId, responseId, children }: Props = $props();

  let timer: ReturnType<typeof setTimeout> | null = null;

  async function handleMouseEnter() {
    timer = setTimeout(async () => {
      const response = await fetch(updateResponseReadStatus(consultationId, responseId), {
          method: "POST",
        });
    }, 5000);
  }

  function handleMouseLeave() {
    if (timer) {
      clearTimeout(timer);
      timer = null;
    }
  }
</script>

<div 
  on:mouseenter={handleMouseEnter}
  on:mouseleave={handleMouseLeave}
>
  {@render children()}
</div>