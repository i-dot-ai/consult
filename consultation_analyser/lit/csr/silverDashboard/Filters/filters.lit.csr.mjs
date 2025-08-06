import { html, css } from 'lit';

import IaiLitBase from '../../../IaiLitBase.mjs';
import Button from '../Button/button.lit.csr.mjs';
import IaiIcon from '../../IaiIcon/iai-icon.mjs';
import SelectInput from '../inputs/SelectInput/select-input.lit.csr.mjs';
import Title from '../Title/title.lit.csr.mjs';
import IconTile from '../IconTile/icon-tile.lit.csr.mjs';
import IaiIconButton from '../../questionsArchive/IaiIconButton/iai-icon-button.lit.csr.mjs';
import ThemeFiltersWarning from '../ThemeFiltersWarning/theme-filters-warning.lit.csr.mjs';
import MultiDropdown from '../inputs/MultiDropdown/multi-dropdown.lit.csr.mjs';


export default class Filters extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        consultationSlug: { type: String },
        themes: { type: Array },
        demoOptions: { type: Object },

        demoFiltersApplied: { type: Function },
        themeFiltersApplied: { type: Function },

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
            iai-filters div[slot="content"] {
                padding-block: 0.5em;
            }
            iai-filters iai-silver-icon-tile {
                font-size: 0.8em;
            }
            iai-filters .theme-title {
                font-weight: bold;
                color: var(--iai-silver-color-text);
            }
            iai-filters iai-silver-button button {
                width: max-content;
                display: flex;
                align-items: center;
                padding-inline: 0.5em;
                gap: 0.5em;
                font-weight: bold;
                color: var(--iai-silver-color-text);
            }
            iai-filters .filters-row {
                display: grid;
                gap: 1em;
            }
            iai-filters .total-themes {
                display: flex;
                flex-direction: column;    
                max-height: max-content;
                padding: 1em;
                font-size: 0.8em;
                white-space: nowrap;
                background: #fcf1f6;
                border-radius: 0.5em;
            }
            iai-filters .total-themes span {
                font-size: 1.5em;
                font-weight: bold;
            }
            iai-filters .filters-row {
                margin-bottom: 1em;
                background: var(--iai-silver-color-light);
                padding: 1em;
                border-radius: 0.5em;
            }
            iai-filters .filters {
                display: flex;
                flex-wrap: wrap;
                gap: 1em;
                align-items: center;
            }
            iai-filters .filters iai-silver-select-input{
                white-space: nowrap;
            }
            iai-filters .top-panel {
                margin-bottom: 2em;
            }
            iai-filters .filters select.govuk-select {
                font-size: 0.9em;
                background: var(--iai-silver-color-light-darker);
            }
            iai-filters iai-multi-dropdown button {
                background: var(--iai-silver-color-light-darker) !important;
            }
            iai-filters .export-button button {
                padding-block: 0.2em;
            }
            iai-filters .filters .demographics-title .icon-container {
                margin: 0;
                color: var(--iai-silver-color-dark);
            }
            iai-filters .filters .govuk-form-group:has(select){
                margin: 0;
            }
            iai-filters .info-container {
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
        this.demoOptions = {};

        this.demoFiltersApplied = () => {};
        this.themeFiltersApplied = () => {};

        this.themeFilters = [];
        this.updateThemeFilters = () => {};

        this.demoFilters = {};
        this.setDemoFilters = () => {};
        
        this.sortType = "";
        this.setSortType = () => {};

        this.sortDirection = "";
        this.setSortDirection = () => {};

        this.applyStaticStyles("iai-filters", Filters.styles);
    }

    render() {
        return html`
            <div class="top-panel">
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
                        ${Object.keys(this.demoOptions).map(category => {
                            return html`
                                <iai-multi-dropdown
                                    .title=${category}
                                    .text=${`${this.demoFilters[category]?.length || 0} filters selected`}
                                    .options=${this.demoOptions[category].map(option => ({
                                        id: option,
                                        checked: Boolean(this.demoFilters[category]?.includes(option)),
                                        title: option,
                                        handleClick: (e) => {
                                            this.setDemoFilters(category, option);
                                        },
                                    }))}
                                ></iai-multi-dropdown>
                            `
                        })}
                    </div>

                    ${this.themeFiltersApplied() || this.demoFiltersApplied() ? html`
                        <iai-silver-button
                            .text=${"Clear filters"}
                            .handleClick=${() => {
                                this.updateThemeFilters();
                                this.setDemoFilters();
                            }}
                        ></iai-silver-button>
                    ` : ""}
                </div>

                ${this.themeFilters.length > 0 ? html`
                    <iai-theme-filters-warning
                        .themes=${this.themes}
                        .themeFilters=${this.themeFilters}
                        .updateThemeFilters=${this.updateThemeFilters}
                    ></iai-theme-filters-warning>
                ` : ""}
            </div>
        `
    }
}
customElements.define("iai-filters", Filters);
