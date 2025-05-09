import { html, css } from "lit";

import IaiLitBase from "../../IaiLitBase.mjs";
import IaiIcon from "../questionsArchive/IaiIcon/iai-icon.mjs";


export default class IaiCsvDownload extends IaiLitBase {
    static styles = [
        IaiLitBase.styles,
        css``
    ]

    static properties = {
        ...IaiLitBase.properties,
        data: {type: Array},
        fileName: { type: String },
    }

    constructor() {
        super();

        this.data = [];
        this.fileName = "data.csv";
    }

    buildCsv(data) {
        if (!data) {
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

    getDownloadUrl = (csvContent) => {
        return "data:text/csv;base64," + btoa(csvContent);
    }

    render() {
        return html`
            <a
                class="govuk-button"
                aria-label="Download themes as CSV"
                title="Download themes as CSV"
                href=${this.getDownloadUrl(this.buildCsv(this.props.data || this.data))}
                download=${this.fileName}
            >
                Download CSV
                <iai-icon
                    name="download"
                ></iai-icon>
            </a>
        `
    }
}
customElements.define("iai-csv-download", IaiCsvDownload);