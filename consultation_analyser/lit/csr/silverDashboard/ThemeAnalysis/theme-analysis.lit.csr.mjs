import { html, css } from 'lit';

import IaiLitBase from '../../../IaiLitBase.mjs';
import IaiAnimatedNumber from '../../IaiAnimatedNumber/iai-animated-number.lit.csr.mjs';
import IaiProgressBar from '../../IaiProgressBar/iai-progress-bar.lit.csr.mjs';
import IaiDataTable from '../../IaiDataTable/iai-data-table.lit.csr.mjs';
import Button from '../Button/button.lit.csr.mjs';
import IaiIcon from '../../IaiIcon/iai-icon.mjs';
import SelectInput from '../inputs/SelectInput/select-input.lit.csr.mjs';
import ThemesTable from '../ThemesTable/themes-table.lit.csr.mjs';
import Title from '../Title/title.lit.csr.mjs';
import IconTile from '../IconTile/icon-tile.lit.csr.mjs';


export default class ThemeAnalysis extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        themes: { type: Array },
        demoData: { type: Array },

        themeFilters: { type: Array },
        updateThemeFilters: { type: Function },

        sortType: { type: String },
        setSortType: { type: Function },

        sortDirection: { type: String },
        setSortDirection: { type: Function },

        demoFilters: { type: Object },
        setDemoFilters: { type: Function },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-theme-analysis div[slot="content"] {
                padding-block: 0.5em;
            }
            iai-theme-analysis iai-silver-icon-tile {
                font-size: 0.8em;
            }
            iai-theme-analysis .theme-title {
                font-weight: bold;
                color: var(--iai-silver-color-text);
            }
            iai-theme-analysis .percentage-cell {
                gap: 0.5em;
                display: flex;
                align-items: center;
            }
            iai-theme-analysis .percentage-cell iai-progress-bar {
                flex-grow: 1;
            }
            iai-theme-analysis .percentage-cell iai-progress-bar .container {
                border-radius: 0.5em;
                background: var(--iai-silver-color-mid);
                border: none;
                opacity: 0.7;
            }
            iai-theme-analysis .percentage-cell iai-progress-bar .bar {
                height: 0.5em;
                border-top-left-radius: 0.5em;
                border-bottom-left-radius: 0.5em;
                background: var(--iai-silver-color-dark);
            }
            iai-theme-analysis iai-silver-button button {
                width: max-content;
                display: flex;
                align-items: center;
                padding-inline: 0.5em;
                gap: 0.5em;
                font-weight: bold;
                color: var(--iai-silver-color-text);
            }
            iai-theme-analysis .filters-row {
                display: grid;
                gap: 1em;
            }
            iai-theme-analysis .total-themes {
                display: flex;
                flex-direction: column;    
                max-height: max-content;
                padding: 1em;
                font-size: 0.8em;
                white-space: nowrap;
                background: #fcf1f6;
                border-radius: 0.5em;
            }
            iai-theme-analysis .total-themes span {
                font-size: 1.5em;
                font-weight: bold;
            }
            iai-theme-analysis .filters-row {
                margin-bottom: 1em;
                background: var(--iai-silver-color-light);
                padding: 1em;
                border-radius: 0.5em;
            }
            iai-theme-analysis .filters {
                display: flex;
                flex-wrap: wrap;
                column-gap: 0.5em;
                row-gap: 1em;
                align-items: center;
            }
            iai-theme-analysis .filters iai-silver-select-input{
                white-space: nowrap;
            }
            iai-theme-analysis .top-panel {
                margin-bottom: 2em;
            }
            iai-theme-analysis .filters select.govuk-select {
                font-size: 0.9em;
                background: #f3f3f5;
            }
            iai-theme-analysis .export-button button {
                padding-block: 0.2em;
            }
            iai-theme-analysis .filters .demographics-title .icon-container {
                margin: 0;
                color: var(--iai-silver-color-dark);
            }
            iai-theme-analysis .filters .govuk-form-group:has(select){
                margin: 0;
            }
            iai-theme-analysis .info-container {
                display: flex;
                justify-content: space-between;
            }
            @media (min-width: 40.0625em) {
                .govuk-form-group {
                    margin-bottom: 0;
                }
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();
        this._NUMBER_ANIMATION_DURATION = 1000;

        this.themes = [];
        this.demoData = [];

        this.themeFilters = [];
        this.updateThemeFilters = () => {};

        this.demoFilters = {};
        this.setDemoFilters = () => {};
        
        this.sortType = "";
        this.setSortType = () => {};

        this.sortDirection = "";
        this.setSortDirection = () => {};

        this.applyStaticStyles("iai-theme-analysis", ThemeAnalysis.styles);
    }
    
    render() {
        return html`
            <iai-silver-panel>
                <div slot="content">
                    <div class="top-panel">
                        <iai-silver-title
                            .text=${"Theme Analysis"}
                            .variant=${"secondary"}
                            .icon=${"lan"}
                            .aside=${html`
                                <iai-silver-button
                                    class="export-button"
                                    .text=${html`
                                        <iai-icon
                                            .name=${"download"}
                                        ></iai-icon>
                                        <span>Export</span>
                                    `}
                                    .handleClick=${() => console.log("export initiated")}
                                ></iai-silver-button>
                            `}
                        ></iai-silver-title>

                        <div class="filters-row">
                            <div class="filters">
                                <iai-silver-select-input
                                    .inputId=${"sort-value"}
                                    .name=${"sort-value"}
                                    .label=${"Sort by:"}
                                    .hideLabel=${false}
                                    .value=${this.sortType}
                                    .options=${[
                                        { value: "frequency", text: "Frequency" },
                                        { value: "alphabetical", text: "A-Z" },
                                    ]}
                                    .handleChange=${(e) => this.setSortType(e.target.value)}
                                    .horizontal=${true}
                                ></iai-silver-select-input>

                                <iai-icon-button .handleClick=${
                                    () => this.setSortDirection(this.sortDirection === "ascending"
                                        ? "descending"
                                        : "ascending"
                                )}>
                                    <iai-icon
                                        slot="icon"
                                        .name=${this.sortDirection === "ascending"
                                            ? "arrow_downward"
                                            : "arrow_upward"
                                        }
                                    ></iai-icon>
                                </iai-icon-button>
                            </div>

                            <div class="filters">
                                <iai-silver-title
                                    class="demographics-title"
                                    .text=${"Demographics"}
                                    .level=${3}
                                ></iai-silver-title>

                                ${Object.keys(this.demoData).map(category => {
                                    const getSlug = (string) => string.toLowerCase().replace(" ", "-");

                                    return html`
                                        <iai-silver-select-input
                                            .inputId=${getSlug(category)}
                                            .name=${getSlug(category)}
                                            .label=${this.toTitleCase(category)}
                                            .hideLabel=${true}
                                            .value=${this.demoFilters[category] || ""}
                                            .placeholder=${`Select ${this.toTitleCase(category)}`}
                                            .options=${(Object.keys(this.demoData[category])).map(key => ({
                                                value: key,
                                                text: this.toTitleCase(key)
                                            }))}
                                            .handleChange=${(e) => {
                                                this.setDemoFilters(category, e.target.value);
                                            }}
                                            .horizontal=${true}
                                        ></iai-silver-select-input>
                                    `
                                })}
                            </div>
                        </div>

                        <div class="info-container">
                            <small>
                                Click themes to select up to 3 for detailed analysis.
                            </small>

                            <small>
                                Total Themes
                                <span>${this.themes.length}<span>
                            </small>
                        </div>
                    </div>

                    <iai-themes-table
                        .themes=${this.themes}
                        .themeFilters=${this.themeFilters}
                        .setThemeFilters=${this.updateThemeFilters}
                    ></iai-themes-table>
                </div>
            </iai-silver-panel>
        `;
    }
}
customElements.define("iai-theme-analysis", ThemeAnalysis);
