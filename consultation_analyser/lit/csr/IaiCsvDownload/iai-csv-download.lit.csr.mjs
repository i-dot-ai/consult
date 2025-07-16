import { html, css } from "lit";

import IaiLitBase from "../../IaiLitBase.mjs";
import IaiIcon from "../IaiIcon/iai-icon.mjs";
import Button from "../silverDashboard/Button/button.lit.csr.mjs";


export default class IaiCsvDownload extends IaiLitBase {
    static styles = [
        IaiLitBase.styles,
        css`
            iai-csv-download a {
                text-decoration: none;
            }
            iai-csv-download a.govuk-button {
                min-height: auto;
                min-width: 13em;
                justify-content: center;
            }
            iai-csv-download iai-silver-button button {
                padding-block: 0.25em;
            }
        `
    ]

    static properties = {
        ...IaiLitBase.properties,
        data: {type: Array},
        fileName: { type: String },
        variant: { type: String }, // "" | "silver"
    }

    constructor() {
        super();

        this.data = [];
        this.fileName = "data.csv";
        this.variant = "";

        this.applyStaticStyles("iai-csv-download", IaiCsvDownload.styles);
    }

    buildCsv(data) {
        if (!data || !Object.keys(data).length > 0) {
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
                class=${!this.variant ? "govuk-button" : ""}
                aria-label="Download themes as CSV"
                title="Download themes as CSV"
                href=${this.getDownloadUrl(this.buildCsv(this.props.data || this.data))}
                download=${this.fileName}
            >
                ${this.variant === "silver"
                    ? html`
                        <iai-silver-button
                            .icon=${"download"}
                            .text=${html`
                                <iai-icon
                                    name="download"
                                ></iai-icon>
                                <span>
                                    Export
                                </span>
                            `}
                        ></iai-silver-button>
                    `
                    : html`
                        Download CSV
                        <iai-icon
                            name="download"
                        ></iai-icon>
                    `}
            </a>
        `
    }
}
customElements.define("iai-csv-download", IaiCsvDownload);