import { html, css } from 'lit';

import IaiLitBase from '../../IaiLitBase.mjs';
import IaiResponseFilters from '../IaiResponseFilters/iai-response-filters.lit.csr.mjs';
import IaiTextInput from '../filters/IaiTextInput/iai-text-input.lit.csr.mjs';
import IaiResponseFilterGroup from '../IaiResponseFilterGroup/iai-response-filter-group.lit.csr.mjs';
import IaiPageTitle from '../IaiPageTitle/iai-page-title.lit.csr.mjs';
import IaiDataTable from '../IaiDataTable/iai-data-table.lit.csr.mjs';


export default class IaiResponseDashboard extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,

        consultationTitle: { type: String },
        questionTitle: { type: String },
        questionText: { type: String },
        stanceOptions: { type: Array },
        themeMappings: { type: Array },
        responses: { type: Array },
        free_text_question_part: { type: Boolean },
        has_individual_data: { type: Boolean },
        has_multiple_choice_question_part: { type: Boolean },
        multiple_choice_summary: { type: Array },

        _searchValue: { type: String },
        _themeSearchValue: { type: String },
        _minWordCount: { type: Number },
        _demographicFilters: { type: Array },
        _themeFilters: { type: Array },
        _themesPanelVisible: { type: Boolean },
        _stanceFilters: { type: Array },
        _evidenceRichFilters: { type: Array },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            .themes-container {
                position: relative;
            }
            .themes-panel {
                position: absolute;
                opacity: 0;
                transition: 0.3s;
                background-color: white;
                z-index: 1;
                width: 100%;
                top: 100%;
                max-height: 30vh;
                left: 0;
                box-shadow: rgba(100, 100, 111, 0.2) 0px 7px 29px 0px;
                padding: 1em;
                overflow: auto;
                pointer-events: none;
            }
            .themes-panel.visible {
                opacity: 1;
                pointer-events: auto;
            }
            .count-display {
                border: 2px solid var(--iai-colour-secondary);
                padding: 0.25em 0.75em;
                background: var(--iai-colour-secondary-transparent);
            }
            iai-response-dashboard .question-text {
                margin-top: 2em;
                font-size: 1.4em;
            }
            iai-response-dashboard hr {
                margin-bottom: 2em;
            }
            iai-response-dashboard .responses-column {
                background: white;
                padding: 1em 2em;
                width: 73.5%;
            }
            iai-response-dashboard .responses-column .title-container {
                display: flex;
                justify-content:space-between;
                align-items: center;
                padding-block: 1em;
            }
            iai-response-dashboard .responses-column .title-container h2 {
                margin: 0;
            }
            iai-response-dashboard .filters-column {
                padding-right: 1.5em;
            }
            iai-response-dashboard .theme-filters-applied {
                margin-bottom: 1em;
            }
            iai-response-dashboard .theme-filters-applied ul {
                list-style: none;
                padding: 0;
                display: flex;
                gap: 1em;
                flex-wrap: wrap;
            }
            iai-response-dashboard .table-container {
                background: white;
                padding: 2em;
            }
            iai-response-dashboard .table-title {
                display: flex;
                justify-content: space-between;
                margin-bottom: 2em;
            }
            iai-response-dashboard .table-title h2 {
                margin: 0;
            }
            iai-response-dashboard .themes-container .input-container {
                position: relative;
            }
            iai-response-dashboard .table-container iai-data-table {
                display: block;    
                max-height: 40em;
                overflow: auto;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();
        
        // Prop defaults
        this._searchValue = "";
        this._themeSearchValue = "";
        this._stanceFilters = [];
        this._evidenceRichFilters = [];
        this._minWordCount = null;
        this._themeFilters = [];
        this._themesPanelVisible = false;
        this._demographicFilters = [];

        this.questionTitle = "";
        this.questionText = "";
        this.consultationTitle = "";
        this.responses = [];
        this.themeMappings = [];
        this.stanceOptions = [];
        this.free_text_question_part = false;
        this.has_individual_data = false;
        this.has_multiple_choice_question_part = false;
        this.multiple_choice_summary = [];

        this.applyStaticStyles("iai-response-dashboard", IaiResponseDashboard.styles);
    }

    firstUpdated() {
        this.responses = this.responses.map(response => ({
            ...response,
            visible: true,
        }));

        window.addEventListener("mousedown", this.handleThemesPanelClose)
    }

    updated(changedProps) {
        if (
            changedProps.has("_stanceFilters") ||
            changedProps.has("_evidenceRichFilters") ||
            changedProps.has("_minWordCount") ||
            changedProps.has("_searchValue")  ||
            changedProps.has("_themeFilters") ||
            changedProps.has("_demographicFilter")
        ) {
            this.applyFilters();
        }
    }

    disconnectedCallback() {
        window.removeEventListener("mousedown", this.handleThemesPanelClose)
    }

    handleSearchInput = (e) => {
        this._searchValue = e.target.value;
    }
    handleStanceChange = (e) => {
        this._stanceFilters = this.addOrRemoveFilter(this._stanceFilters, e.target.value);
    }
    handleEvidenceRichChange = (e) => {
        this._evidenceRichFilters = this.addOrRemoveFilter(this._evidenceRichFilters, e.target.value);
    }
    handleMinWordCountInput = (e) => {
        this._minWordCount = parseInt(e.target.value);
    }
    handleThemeFilterChange = (e) => {
        this._themeFilters = this.addOrRemoveFilter(this._themeFilters, e.target.value);
    }
    handleDemographicChange = (e) => {
        this._demographicFilters = this.addOrRemoveFilter(this._demographicFilters, e.target.value);
    }

    getVisibleResponseTotal() {
        return this.responses.filter(response => response.visible).length;
    }

    handleThemesPanelClose = (e) => {
        const themesContainerEl = this.querySelector(".themes-container");

        if (!themesContainerEl) {
            return;
        }

        if (!themesContainerEl.contains(e.target)) {
            this._themesPanelVisible = false;
        }
    }

    calculateResponsesHeight = () => {
        const filtersEl = document.getElementsByTagName("iai-response-filters")[0];
        const titleEl = document.querySelector("iai-response-dashboard .title-container");
        return filtersEl && titleEl ? filtersEl.offsetHeight - titleEl.offsetHeight : 0;
    }

    addOrRemoveFilter = (filters, newFilter) => {
        if (filters.includes(newFilter)) {
            return filters.filter(filter => filter !== newFilter);
        } else {
            return [...filters, newFilter];
        }
    }

    applyFilters = () => {
        this.responses = this.responses.map(response => ({
            ...response,
            visible: this.getResponseVisibility(response),
        }))
    }

    getResponseVisibility = (response) => {
        let visible = true;

        // filter by search box text
        if (
            this._searchValue &&
            !response.free_text_answer_text.toLocaleLowerCase().includes(this._searchValue.toLocaleLowerCase()) &&
            !response.identifier.toLocaleLowerCase().includes(this._searchValue.toLocaleLowerCase()) &&
            !response.multiple_choice_answer.join(",").toLocaleLowerCase().includes(this._searchValue.toLocaleLowerCase())
        ) {
            visible = false;
        }

        // TODO: filter by demographic
        // if (
        //     (response.individual === "individual" && !this._demographicFilters.includes("individual")) ||
        //     (response.individual === "" && !this._demographicFilters.includes("organisation"))
        // ) {
        //     visible = false;
        // }
        
        // filter by themes selected
        if (this._themeFilters.length > 0) {
            if (!response.themes.find(theme => this._themeFilters.includes(theme.id))) {
                visible = false;
            }
        }

        // filter by stances selected
        if (this._stanceFilters.length > 0) {
            if (!this._stanceFilters.includes(response.sentiment_position)) {
                visible = false;
            }
        }

        // filter by min word count
        if (this._evidenceRichFilters) {
            // TODO: Evidence Rich filter logic here
        }

        // filter by min word count
        if (this._minWordCount) {
            if (response.free_text_answer_text.length < this._minWordCount) {
                visible = false;
            }
        }

        return visible;
    }

    getAllThemes() {
        return this.responses.map(response => response.themes);
    }

    themeFilterInputVisible = (themeMapping) => {
        return (
            this._themeFilters.includes(themeMapping.value) ||
            themeMapping.label.toLocaleLowerCase().includes(this._themeSearchValue.toLocaleLowerCase())
        )
    } 

    render() {
        const visibleResponses = this.responses.filter(response => response.visible);

        return html`
            <div class="govuk-grid-row govuk-!-margin-top-5">
                <div class="govuk-grid-column-full">
                    <iai-page-title
                        .title=${html`
                            <div style="display: flex;">
                                <span style="margin-right: 1em;">${this.questionTitle}</span>
                                <span class="govuk-caption-m count-display">
                                    <strong>${this.responses.length}</strong> responses
                                </span>
                            </div>
                        `}
                        .subtitle=${this.consultationTitle}
                    ></iai-page-title>

                    <div class="question-text">
                        <iai-expanding-text
                            .text=${this.questionText}
                            .lines=${2}
                        ></iai-expanding-text>
                    </div>
                </div>
            </div>

            ${this.themeMappings.length > 0
                ? html`
                    <div class="govuk-grid-row govuk-!-margin-top-5">
                        <div class="govuk-grid-column-full">
                            <div class="table-container">

                                <div class="table-title">
                                    <h2 class="govuk-heading-m">
                                        Themes
                                    </h2>

                                    <!-- TODO:
                                        <button>Download CSV</button>
                                    -->
                                </div>

                                <div class="theme-filters-applied">
                                    <ul>
                                        ${this._themeFilters.map(themeFilterId => html`
                                            <li>
                                                <iai-chip
                                                    .label=${this.themeMappings
                                                        .find(themeMapping => themeMapping.value == themeFilterId).label
                                                    }
                                                    .handleClick=${_ => this._themeFilters = this._themeFilters.filter(
                                                        currThemeFilterId => currThemeFilterId != themeFilterId
                                                    )}
                                                ></iai-chip>
                                            </li>
                                        `)}
                                    </ul>
                                </div>

                                <iai-data-table
                                    .data=${this.themeMappings
                                        .filter(themeMapping => (
                                            this._themeFilters.includes(themeMapping.value) || this._themeFilters.length == 0
                                        ))
                                        .map(themeMapping => (
                                            {
                                                "Theme name and description": html`
                                                    <iai-expanding-pill
                                                        .label=${themeMapping.label}
                                                        .body=${themeMapping.description}
                                                        .initialExpanded=${true}
                                                    ></iai-expanding-pill>
                                                `,
                                                "Total mentions": themeMapping.count,
                                            }
                                        ))
                                    }
                                ></iai-data-table>
                            </div>
                        </div>
                    </div>
                ` 
                : ""
            }

            ${this.multiple_choice_summary.length > 0
                ? html`
                    <div class="govuk-grid-row govuk-!-margin-top-5">
                        <div class="govuk-grid-column-full">
                            <div class="table-container">
                                <div class="table-title">
                                    <h2 class="govuk-heading-m">
                                        Multiple-Choice Responses
                                    </h2>
                                </div>

                                <iai-data-table
                                    .data=${this.multiple_choice_summary.map(item => ({
                                        "Answer": Object.keys(item)[0],
                                        "Count": Object.values(item)[0],
                                    }))}
                                ></iai-data-table>
                            </div>
                        </div>
                    </div>
                `
                : ""}

            <div class="govuk-grid-row govuk-!-margin-top-5">
                <div class="govuk-grid-column-one-quarter-from-desktop filters-column">
                    <iai-response-filters>
                        <form slot="filters" method="GET">
                            <div class="iai-filter__options">

                                ${this.free_text_question_part
                                    ? html`
                                        <iai-response-filter-group title="Themes">
                                            <div
                                                slot="content"
                                                class="govuk-checkboxes govuk-checkboxes--small"
                                                data-module="govuk-checkboxes"
                                                data-govuk-checkboxes-init=""
                                            >
                                                <div class="themes-container">
                                                    <div
                                                        class="input-container"
                                                        @focusin=${() => this._themesPanelVisible = true}
                                                    >
                                                        <iai-text-input
                                                            inputId="responses-search-input"
                                                            name="responses-search"
                                                            label="Search"
                                                            hideLabel=${true}
                                                            placeholder="Search..."
                                                            value=${this._themeSearchValue}
                                                            .handleInput=${e => this._themeSearchValue = e.target.value}
                                                        ></iai-text-input>

                                                        <div class=${"themes-panel" + (this._themesPanelVisible ? " visible" : "")}>
                                                            ${this.themeMappings.map(themeMapping => this.themeFilterInputVisible(themeMapping)
                                                                ? html`
                                                                    <iai-checkbox-input
                                                                        name="thememappings-filter"
                                                                        .inputId=${themeMapping.inputId}
                                                                        .label=${themeMapping.label}
                                                                        .value=${themeMapping.value}
                                                                        .checked=${this._themeFilters.includes(themeMapping.value)}
                                                                        .handleChange=${this.handleThemeFilterChange}
                                                                        @focusin=${() => this._themesPanelVisible = true}
                                                                    ></iai-checkbox-input>
                                                                `
                                                                : ""
                                                            )}
                                                        </div>
                                                    </div>

                                                    ${this._themeFilters.length > 0
                                                        ? html`
                                                            <div class="theme-filters-applied">
                                                                <ul>
                                                                    ${this._themeFilters.map(themeFilterId => html`
                                                                        <li>
                                                                            <iai-chip
                                                                                .label=${this.themeMappings
                                                                                    .find(themeMapping => themeMapping.value == themeFilterId).label
                                                                                }
                                                                                .handleClick=${_ => this._themeFilters = this._themeFilters.filter(
                                                                                    currThemeFilterId => currThemeFilterId != themeFilterId
                                                                                )}
                                                                            ></iai-chip>
                                                                        </li>
                                                                    `)}
                                                                </ul>
                                                            </div>
                                                        `
                                                        : ""}
                                                </div>
                                            </div>
                                        </iai-response-filter-group>

                                        <hr />
                                    `
                                    : ""
                                }

                                ${this.has_individual_data ? html`
                                    <iai-response-filter-group title="Respondent type">
                                        <div
                                            slot="content"
                                            class="govuk-checkboxes govuk-checkboxes--small"
                                            data-module="govuk-checkboxes"
                                            data-govuk-checkboxes-init=""
                                        >
                                            <iai-checkbox-input
                                                name="demographic-filter"
                                                inputId="demographic-individual"
                                                label="Individual"
                                                value="individual"
                                                .handleChange=${this.handleDemographicChange}
                                            ></iai-checkbox-input>
                                            <iai-checkbox-input
                                                name="demographic-filter"
                                                inputId="demographic-organisation"
                                                label="Organisation"
                                                value="organisation"
                                                .handleChange=${this.handleDemographicChange}
                                            ></iai-checkbox-input>
                                        </div>
                                    </iai-response-filter-group>

                                    <hr />
                                ` : ""}


                                <iai-response-filter-group title="Response sentiment">
                                    <div
                                        slot="content"
                                        class="govuk-checkboxes govuk-checkboxes--small"
                                        data-module="govuk-checkboxes"
                                        data-govuk-checkboxes-init=""
                                    >
                                        ${this.stanceOptions.map(option => html`
                                            <iai-checkbox-input
                                                name=${option.name}
                                                inputId=${option.inputId}
                                                label=${option.label}
                                                value=${option.value}
                                                .handleChange=${this.handleStanceChange}
                                            ></iai-checkbox-input>
                                        `)}
                                    </div>
                                </iai-response-filter-group>

                                <hr />

                                <iai-response-filter-group title="Evidence-rich responses">
                                    <div
                                        slot="content"
                                        class="govuk-checkboxes govuk-checkboxes--small"
                                        data-module="govuk-checkboxes"
                                        data-govuk-checkboxes-init=""
                                    >
                                        <iai-checkbox-input
                                            name="evidence-rich"
                                            inputId="show-evidence-rich"
                                            label="Only show evidence-rich"
                                            value="evidence-rich"
                                            .handleChange=${this.handleEvidenceRichChange}
                                        ></iai-checkbox-input>
                                    </div>
                                </iai-response-filter-group>
                        
                                ${this.free_text_question_part 
                                    ? html`
                                        <hr />
                                        
                                        <iai-response-filter-group title="Response word count">
                                            <div slot="content">
                                                <iai-number-input
                                                    inputId="min-word-count"
                                                    name="min-word-count"
                                                    label="Minimum:"
                                                    value=${this._minWordCount}
                                                    .handleInput=${this.handleMinWordCountInput}
                                                    .horizontal=${true}
                                                ></iai-number-input>
                                            </div>
                                        </iai-response-filter-group>
                                    `
                                    : ""
                                }
                            </div>
                        </form>
                    </iai-response-filters>
                </div>

                <div class="govuk-grid-column-three-quarters-from-desktop responses-column">
                    <div class="title-container">
                    
                        <h2 class="govuk-heading-m">
                            Individual responses
                        </h2>

                        <span class="govuk-caption-m count-display">
                            Viewing <strong>${visibleResponses.length}</strong> responses
                        </span>

                        <iai-text-input
                            inputId="responses-search-input"
                            name="responses-search"
                            label="Search"
                            hideLabel=${true}
                            placeholder="Search..."
                            value=${this._searchValue}
                            .handleInput=${this.handleSearchInput}
                        ></iai-text-input>
                    </div>

                    <iai-responses
                        style="height: ${this.calculateResponsesHeight()}px;"
                        .responses=${visibleResponses}
                        .renderResponse=${response => html`
                            <iai-response
                                role="listitem"
                                .id=${response.inputId}
                                .identifier=${response.identifier}
                                .individual=${response.individual}
                                .sentiment_position=${response.sentiment_position}
                                .free_text_answer_text=${response.free_text_answer_text}
                                .demographic_data=${response.demographic_data}
                                .themes=${response.themes}
                                .has_multiple_choice_question_part=${this.has_multiple_choice_question_part}
                                .multiple_choice_answer=${response.multiple_choice_answer}
                                .searchValue=${this._searchValue}
                            ></iai-response>
                        `}
                    ></iai-responses>
                </div>
            </div>
        `;
    }
}
customElements.define("iai-response-dashboard", IaiResponseDashboard);