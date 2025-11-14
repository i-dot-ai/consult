<script lang="ts">
  import { getApiAnswerFlagUrl } from "../../../global/routes";
  import { createFetchStore } from "../../../global/stores";

  import Button from "../../inputs/Button/Button.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import Flag2 from "../../svg/material/Flag2.svelte";

  interface Props {
    consultationId: string;
    questionId: string;
    answerId: string;
    isFlagged: boolean;
    resetData: () => void;
    toggleFlagMock?: (url: string, method: string) => Promise<void>;
  }

  let {
    consultationId,
    questionId,
    answerId,
    isFlagged,
    resetData,
    toggleFlagMock,
  }: Props = $props();

  const { load: toggleFlag } = createFetchStore();
</script>

<div class="py-2">
  <Button
    title="Flag response"
    size="xs"
    variant="ghost"
    handleClick={async () => {
      let toggle = toggleFlagMock || toggleFlag;
      await toggle(
        getApiAnswerFlagUrl(consultationId, questionId, answerId),
        "PATCH",
      );

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
