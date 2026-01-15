<script lang="ts">
  import { getApiAnswerFlagUrl } from "../../../global/routes";
  import { createQueryStore } from "../../../global/stores";

  import Button from "../../inputs/Button/Button.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import Flag2 from "../../svg/material/Flag2.svelte";

  interface Props {
    consultationId: string;
    questionId: string;
    answerId: string;
    isFlagged: boolean;
    resetData: () => void;
    toggleFlagMock?: () => Promise<void>;
  }

  let {
    consultationId,
    answerId,
    isFlagged,
    resetData,
    toggleFlagMock,
  }: Props = $props();

  const toggleFlagQuery = $derived(createQueryStore({
    url: getApiAnswerFlagUrl(consultationId, answerId),
    method: "PATCH",
  }));
</script>

<div class="py-2">
  <Button
    title="Flag response"
    size="xs"
    variant="ghost"
    handleClick={async () => {
      let toggle = toggleFlagMock || $toggleFlagQuery.fetch;
      await toggle();

      resetData();
    }}
    highlighted={isFlagged}
    highlightVariant="none"
  >
    <MaterialIcon color={isFlagged ? "fill-primary" : "fill-neutral-500"}>
      <Flag2 fill={isFlagged} />
    </MaterialIcon>
  </Button>
</div>
