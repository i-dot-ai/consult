<script lang="ts">
    import { onMount } from "svelte";
    import { slide } from "svelte/transition";

    import { createFetchStore } from "../../../global/stores";

    import Button from "../../inputs/Button/Button.svelte";
    import Popover from "../../inputs/Popover/Popover.svelte";
    import SearchableSelect from "../../inputs/SearchableSelect.svelte";
    import MaterialIcon from "../../MaterialIcon.svelte";
    import Check from "../../svg/material/Check.svelte";
    import Close from "../../svg/material/Close.svelte";
    import EditSquare from "../../svg/material/EditSquare.svelte";
    import Tag from "../../Tag/Tag.svelte";
    import Title from "../../Title.svelte";
    import TitleRow from "../TitleRow.svelte";
    import AutoRenew from "../../svg/material/AutoRenew.svelte";
    import { type ResponseTheme, type SearchableSelectOption } from "../../../global/types";


    function removeTheme(id: string) {
        stagedThemes = stagedThemes.filter(theme => theme.id !== id);
    }
    function addTheme(option: SearchableSelectOption) {
        if (stagedThemes.find(theme => theme.id === option.value)) {
            return;
        }

        stagedThemes = [...stagedThemes, {
            id: option.value,
            name: option.label,
            description: option.description || "",
        }]
    }

    function submit() {
        console.log(`submitting update for answer ${id}:`, stagedThemes, stagedEvidenceRich);

        updateAnswer(`/api/responses/update`, "PUT", {
            "themes": stagedThemes.map(theme => theme.id).join(","),
            "evidenceRich": stagedEvidenceRich,
        } as unknown as BodyInit);
    }

    let {
        id = "",
        themes = [],
        themeOptions = [],
        evidenceRich = false,
        setEditing = () => {},
    } = $props();

    let stagedThemes: ResponseTheme[] = $state([]);
    let stagedEvidenceRich = $state(false);
    let panelOpen: boolean = $state(false);

    const {
        loading: isSubmitting,
        error: submitError,
        load: updateAnswer,
        data: answerData,
    } = createFetchStore();


    onMount(() => {
        resetStaged();
    })

    function resetStaged() {
        stagedThemes = [...themes];
        stagedEvidenceRich = evidenceRich;
        isSubmitting.set(false);
        submitError.set("");
    }
</script>


<Popover
    arrow={false}
    border={false}
    open={panelOpen}
    handleOpenChange={newOpen => {
        panelOpen = newOpen;
        setEditing(newOpen);
    }}
>
    <div slot="trigger">
        <MaterialIcon color="fill-neutral-500">
            <EditSquare />
        </MaterialIcon>
    </div>

    <div slot="panel" class="w-full bg-white p-4 shadow-lg">
        <TitleRow level={3} title="Edit Response Labels">
            <div slot="aside">
                <Button variant="ghost" handleClick={() => panelOpen = false}>
                    <MaterialIcon color="fill-neutral-500">
                        <Close />
                    </MaterialIcon>
                </Button>
            </div>
        </TitleRow>

        <div>
            <Title level={4} text="Themes" />

            <ul class="flex flex-wrap gap-2 items-center justify-start my-1">
                {#each stagedThemes as theme}
                    <Tag>
                        {theme.name}

                        <Button variant="ghost" handleClick={() => removeTheme(theme.id)}>
                            <MaterialIcon color="fill-neutral-500">
                                <Close />
                            </MaterialIcon>
                        </Button>
                    </Tag>
                {/each}
            </ul>

            <div class="my-2">
                <SearchableSelect
                    label="Add Themes"
                    options={themeOptions.map(theme => ({
                        value: theme.id,
                        label: theme.name,
                        description: theme.description,
                        disabled: false,
                    }))}
                    selectedValues={stagedThemes.map(theme => theme.id)}
                    handleChange={(option: SearchableSelectOption) => {
                        if (option.value) {
                            addTheme(option.value);
                        }
                    }}
                />
            </div>
        </div>

        <div class="my-2">
            <Title level={4} text="Evidence-rich" />

            <div class="flex items-center gap-2 my-1">
                <Button
                    size="xs"
                    handleClick={() => stagedEvidenceRich = true}
                    highlighted={stagedEvidenceRich}
                    highlightVariant="approve"
                >
                    Evidence-rich
                </Button>

                <Button
                    size="xs"
                    handleClick={() => stagedEvidenceRich = false}
                    highlighted={!stagedEvidenceRich}
                    highlightVariant="approve"
                >
                    Not evidence-rich
                </Button>
            </div>
        </div>

        <hr class="my-4" />

        {#if $submitError}
            <small class="block my-2 text-red-500" transition:slide>{$submitError}</small>
        {/if}

        <div class="w-full flex justify-end">
            <div class="w-1/2 mr-1">
                <Button size="sm" handleClick={() => resetStaged()} fullWidth={true}>
                    <div class="flex justify-center items-center gap-2 w-full py-0.5">
                        <MaterialIcon color="fill-neutral-500">
                            <AutoRenew />
                        </MaterialIcon>

                        Reset
                    </div>
                </Button>
            </div>

            <div class="w-1/2 ml-1">
                <Button variant="approve" size="sm" handleClick={() => submit()} fullWidth={true}>
                    <div class="flex justify-center items-center gap-2 w-full py-0.5">
                        <MaterialIcon>
                            <Check />
                        </MaterialIcon>

                        <span class="whitespace-nowrap">
                            {$isSubmitting ? "Saving..." : "Save Changes"}
                        </span>
                    </div>
                </Button>
            </div>
        </div>
    </div>
</Popover>