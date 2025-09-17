<script lang="ts">
    import Button from "../inputs/Button/Button.svelte";
    import MaterialIcon from "../MaterialIcon.svelte";
    import Download from "../svg/material/Download.svelte";


    interface Props {
        data: any[];
        fileName: string;
    }

    let {
        data = [],
        fileName = "data.csv",
    }: Props = $props();

    const buildCsv = (data: any[]) => {
        if (!data || Object.keys(data).length <= 0) {
            return "";
        }

        const localData = Array.isArray(data) ? data : [data]
        
        const keys = Object.keys(data[0]);
        const rows = [
            keys.join(","),
            ...localData.map(row => keys.map(key => JSON.stringify(row[key] ?? "")).join(","))
        ];
        return rows.join("\n");
    }

    const getDownloadUrl = (csvContent: string) => {
        return "data:text/csv;base64," + btoa(unescape(encodeURIComponent(csvContent)));
    }
</script>

<a
    aria-label="Download themes as CSV"
    title="Download themes as CSV"
    href={getDownloadUrl(buildCsv(data))}
    download={fileName}
    data-testid="csv-download"
>
    <Button size="sm">
        <MaterialIcon color="fill-neutral-700">
            <Download />
        </MaterialIcon>

        <span class="text-xs text-neutral-700">
            Export
        </span>
    </Button>
</a>