<script lang="ts">
    import { getPercentage } from "../../../global/utils";

    import MaterialIcon from "../../MaterialIcon.svelte";
    import Person from "../../svg/material/Person.svelte";
    import Panel from "../Panel/Panel.svelte";    
    import Calendar from "../../svg/material/Calendar.svelte";
    import Shield from "../../svg/material/Shield.svelte";
    import LocationOn from "../../svg/material/LocationOn.svelte";

    import RespondentSidebarItem from "../RespondentSidebarItem/RespondentSidebarItem.svelte";


    interface Props {
        respondentType: string;
        geographicLocation: string;
        selfReportedDisability: string;
        sector: string;
        stakeholderName: string;
        questionsAnswered: number;
        totalQuestions: number;
    }

    let {
        respondentType = "",
        geographicLocation = "",
        selfReportedDisability = "",
        sector = "",
        stakeholderName = "",
        questionsAnswered = 0,
        totalQuestions = 0,
    }: Props = $props();
</script>

<Panel>
    <div class="flex items-center gap-2 mb-6">
        <MaterialIcon size="1.5rem" color="fill-neutral-700">
            <Person />
        </MaterialIcon>
        <h2 class="text-sm">Respondent Demographics</h2>
    </div>

    <div class="pl-4">
        <RespondentSidebarItem
            title="Respondent Type"
            subtitle={respondentType}
            icon={Person}
        />

        <RespondentSidebarItem
            title="Geographic Location"
            subtitle={geographicLocation}
            icon={LocationOn}
        />

        <RespondentSidebarItem
            title="Self-Reported Disability"
            subtitle={selfReportedDisability}
            icon={Shield}
        />

        <RespondentSidebarItem
            title="Sector"
            subtitle={sector}
            icon={Person}
        />

        <RespondentSidebarItem
            title="Stakeholder Name"
            subtitle={stakeholderName}
            icon={Person}
            editable={true}
            updateSubtitle={(newSubtitle) => console.log(`Updating ${stakeholderName} to ${newSubtitle}`)}
        />

        <hr class="my-4" />

        <RespondentSidebarItem
            title="Questions Answered"
            subtitle={`${getPercentage(questionsAnswered, totalQuestions)}% (${questionsAnswered}/${totalQuestions})`}
            icon={Calendar}
        />
    </div>
</Panel>