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
        resetData: Function;
        isFlagged: boolean;
    }

    let {
        consultationId,
        questionId,
        answerId,
        resetData,
        isFlagged,
    }: Props = $props();

    const {
        loading: isSubmitting,
        error: submitError,
        load: toggleFlag,
        data: answerData,
    } = createFetchStore();
</script>

<div class="py-2">
    <Button
        title="Flag response"
        size="xs"
        variant="ghost"
        handleClick={async () => {
            await toggleFlag(getApiAnswerFlagUrl(consultationId, questionId, answerId), "PATCH");
            resetData();
        }}
    >
        <MaterialIcon color={isFlagged ? "fill-primary" : "fill-neutral-500"}>
            <Flag2 fill={isFlagged} />
        </MaterialIcon>
    </Button>
</div>