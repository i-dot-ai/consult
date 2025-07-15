import { html, css } from 'lit';

import IaiLitBase from '../../../../IaiLitBase.mjs';
import Title from '../../Title/title.lit.csr.mjs';
import Panel from '../../Panel/panel.lit.csr.mjs';
import Tag from '../../Tag/tag.lit.csr.mjs';
import ToggleInput from '../../../inputs/ToggleInput/iai-toggle-input.lit.csr.mjs';
import SelectInput from '../../inputs/SelectInput/select-input.lit.csr.mjs';
import Button from '../../Button/button.lit.csr.mjs';
import ThemeFiltersWarning from '../../ThemeFiltersWarning/theme-filters-warning.lit.csr.mjs';


export default class ResponseRefinement extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        responses: { type: Array },
        highlightMatches: { type: Boolean },
        demoData: { type: Object },
        demoOptions: { type: Object },
        themes: { type: Array },
        
        searchValue: { type: String },
        setSearchValue: { type: Function },

        searchMode: { type: Boolean },
        setSearchMode: { type: Function },

        evidenceRich: { type: Boolean },
        setEvidenceRich: { type: Function },

        demoFilters: { type: Array },
        setDemoFilters: { type: Function },

        highlightMatches: { type: Boolean },
        setHighlightMatches: { type: Function },

        demoFilters: { type: Object },
        setDemoFilters: { type: Function },

        themeFilters: { type: Array },
        updateThemeFilters: { type: Function },

        _settingsVisible: { type: Boolean },
        _themeFiltersVisible: { type: Boolean },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-response-refinement label,
            iai-response-refinement select,
            iai-response-refinement input {
                font-size: 0.9em !important;
            }
            iai-response-refinement .filters {
                display: flex;
                gap: 1em;
                width: 100%;
                flex-direction: column;
            }
            iai-response-refinement iai-silver-select-input {
                display: block;
                width: max-content;
            }
            iai-response-refinement .search-container {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 0.5em;
            }
            iai-response-refinement .search-container iai-silver-search-box {
                flex-grow: 1;
            }
            iai-response-refinement .search-container iai-silver-search-box .clear-button {
                top: 70%;
            }
            iai-response-refinement iai-silver-tag .material-symbols-outlined {
                font-size: 2em;
            }
            iai-response-refinement .tag {
                width: 100%;
            }
            iai-response-refinement input[type="checkbox"] {
                width: auto;
                filter: grayscale(0.5) hue-rotate(75deg);
                cursor: pointer;
            },
            iai-response-refinement label {
                cursor: pointer;
                white-space: nowrap;
            }
            iai-response-refinement .filters-row {
                display: flex;
                align-items: flex-end;
                flex-wrap: wrap;
                gap: 1em;
            }
            iai-response-refinement .theme-filter-list {
                list-style: none;
                padding-left: 0;
                margin: 0;
            }
            iai-response-refinement .theme-filter-list li {
                display: flex;
                gap: 0.5em;
                justify-content: flex-start;
                margin-bottom: 0.5em;
            }
            iai-response-refinement iai-silver-select-input .govuk-form-group {
                margin-bottom: 0;
            }
            iai-response-refinement iai-theme-filters-warning {
                width: 100%;
            }
            iai-response-refinement .popup-button .popup-panel {
                position: absolute;
                top: 2em;
                width: max-content;
                right: 0;
                background: white;
                padding: 1em;
                margin: 0;
                z-index: 2;
                border: 1px solid var(--iai-silver-color-mid);
                border-radius: 0.5em;
                opacity: 1;
                transition: opacity 0.3s ease-in-out;
                box-shadow: rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0.1) 0px 4px 6px -1px, rgba(0, 0, 0, 0.1) 0px 2px 4px -2px;
            }
            iai-response-refinement .popup-button {
                position: relative;
            }
            iai-response-refinement .popup-button .popup-panel.themes-panel {
                right: unset;
                left: 0;
            }
            iai-response-refinement .popup-panel .content {
                display: flex;
                align-items: center;
                gap: 1em;
            }
            iai-response-refinement .popup-button .icon-container {
                margin-bottom: 0.5em;
            }
            iai-response-refinement .popup-button iai-silver-title {
                color: var(--iai-silver-color-dark);
                cursor: pointer;
            }
            iai-response-refinement .popup-button .popup-button__body {
                position: relative;
            }
            iai-response-refinement .popup-button .popup-button__body button {
                line-height: 2em;
                background: var(--iai-silver-color-light);
                border: none;
                border-radius: 0.3em;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.demoData = {};
        this.demoOptions = {};
        this.themes = [];

        this.searchValue = "";
        this.setSearchValue = () => {};

        this.searchMode = "keyword";
        this.setSearchMode = () => {};

        this.highlightMatches = true;
        this.setHighlightMatches = () => {};

        this.evidenceRich = false;
        this.setEvidenceRich = () => {};

        this.demoFilters = {};
        this.setDemoFilters = () => {};

        this.themeFilters = [];
        this.updateThemeFilters = () => {};

        this._settingsVisible = false;
        this._themeFiltersVisible = false;
        
        this.applyStaticStyles("iai-response-refinement", ResponseRefinement.styles);
    }

    render() {
        return html`
            <iai-silver-panel>
                <div slot="content">
                    <iai-silver-title
                        .icon=${"filter_alt"}
                        .text=${`Response refinement`}
                        .subtext=${"Filter and search through individual responses to this question."}
                        .level=${2}
                    ></iai-silver-title>

                    <div class="filters">
                        <iai-silver-select-input
                            .inputId=${"search-mode"}
                            .name=${"search-mode"}
                            .label=${"Search:"}
                            .hideLabel=${false}
                            .value=${this.searchMode}
                            .options=${[
                                { value: "keyword", text: "Keyword" },
                                { value: "semantic", text: "Semantic" },
                            ]}
                            .handleChange=${(e) => this.setSearchMode(e.target.value)}
                            .horizontal=${true}
                        ></iai-silver-select-input>

                        ${this.searchMode === "semantic" ? html`
                            <iai-silver-tag
                                .status=${"Open"}
                                .icon=${"network_intelligence"}
                                .text=${"Semantic search uses AI to understand the meaning behind your search terms, finding responses with similar concepts even if they don't contain the exact words."}
                            ></iai-silver-tag>
                        ` : ""}

                        <div class="search-container">
                            <iai-silver-search-box
                                .inputId=${"search-value"}
                                .name=${"search-value"}
                                .label=${"Search"}
                                .placeholder=${this.searchMode == "keyword"
                                    ? "Search by keywords in questions, themes or descriptions..."
                                    : "Search by concepts like 'pollution sources', 'health effects', 'solutions'..."
                                }
                                .value=${this.searchValue}
                                .handleInput=${(e) => this.setSearchValue(e.target.value.trim())}
                            ></iai-silver-search-box>

                            <div class="popup-button">
                                <iai-icon-button
                                    title="Search settings"
                                    @click=${() => this._settingsVisible = !this._settingsVisible}
                                >
                                    <iai-icon
                                        slot="icon"
                                        name="settings"
                                        .color=${this._settingsVisible ? "var(--iai-silver-color-dark)" : "var(--iai-silver-color-text)"}
                                        .fill=${1}
                                    ></iai-icon>
                                </iai-icon-button>

                                <div class="popup-panel" style=${`
                                    opacity: ${this._settingsVisible ? 1 : 0};
                                    pointer-events: ${this._settingsVisible ? "auto" : "none"};
                                `}>
                                    <iai-silver-title
                                        .text=${"Search Settings"}
                                        .variant=${"secondary"}
                                    ></iai-silver-title>
                                    <div class="content">
                                        <iai-toggle-input
                                            name=${"highligh-matches"}
                                            .handleChange=${(e) => {
                                                this.setHighlightMatches(!this.highlightMatches);
                                            }}
                                            inputId=${"highligh-matches-toggle"}
                                            label=${"Highlight Matches"}
                                            value=${this.highlightMatches}
                                            .checked=${this.highlightMatches}
                                        ></iai-toggle-input>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div >
                            <iai-toggle-input
                                name=${"evidence-rich"}
                                .handleChange=${(e) => {
                                    this.setEvidenceRich(!this.evidenceRich);
                                }}
                                inputId=${"evidence-rich-input"}
                                label=${"Evidence-rich responses"}
                                value=${this.evidenceRich}
                                .checked=${this.evidenceRich}
                            ></iai-toggle-input>
                        </div>
                        
                        <div class="filters-row">
                            ${Object.keys(this.demoOptions).map(key => html`
                                <iai-silver-select-input
                                    .inputId=${`demo-filter-${key}`}
                                    .name=${"demo-filter"}
                                    .label=${this.toTitleCase(key)}
                                    .hideLabel=${false}
                                    .value=${this.demoFilters[key] || ""}
                                    .placeholder=${this.toTitleCase(key)}
                                    .options=${
                                        this.demoOptions[key].map(option => ({
                                            value: option,
                                            text: option
                                        }))
                                    }
                                    .handleChange=${(e) => {
                                        this.setDemoFilters(key, e.target.value);
                                    }}
                                    .horizontal=${false}
                                ></iai-silver-select-input>
                            `)}
                        </div>

                        <div class="filters-row">
                            <div class="popup-button">
                                <iai-silver-title
                                    .level=${3}
                                    .text=${"Themes"}
                                    @click=${() => this._themeFiltersVisible = !this._themeFiltersVisible}
                                ></iai-silver-title>

                                <div class="popup-button__body">
                                    <iai-silver-button
                                        .text=${`${this.themeFilters.length} themes selected`}
                                        .handleClick=${() => this._themeFiltersVisible = !this._themeFiltersVisible}
                                    ></iai-silver-button>

                                    ${this.themes.length > 0 ? html`
                                        <div class="popup-panel themes-panel" style=${`
                                            opacity: ${this._themeFiltersVisible ? 1 : 0};
                                            pointer-events: ${this._themeFiltersVisible ? "auto" : "none"};
                                        `}>
                                            <div class="content">
                                                <ul class="theme-filter-list">
                                                    ${this.themes.map(theme => html`
                                                        <li>
                                                            <input
                                                                type="checkbox"
                                                                class="theme-checkbox"
                                                                id=${"responses-theme-filters" + theme.id}
                                                                name="theme-filters"
                                                                .value=${theme.id}
                                                                .checked=${this.themeFilters.includes(theme.id)}
                                                                @click=${(e) => {
                                                                    this.updateThemeFilters(theme.id);
                                                                }}
                                                            />
                                                            <label for=${"responses-theme-filters" + theme.id}>
                                                                ${theme.title}
                                                            </label>
                                                        </li>
                                                    `)}
                                                </ul>
                                            </div>
                                        </div>
                                    ` : ""}
                                </div>
                            </div>
                        </div>

                        <div class="filters-row">
                            ${this.themeFilters.length > 0 ? html`
                                <iai-theme-filters-warning
                                    .themes=${this.themes}
                                    .themeFilters=${this.themeFilters}
                                    .updateThemeFilters=${this.updateThemeFilters}
                                ></iai-theme-filters-warning>
                            ` : ""}
                        </div>
                    </div>
                </div>
            </iai-silver-panel>
        `
    }
}
customElements.define("iai-response-refinement", ResponseRefinement);