import { html, css } from 'lit';

import IaiLitBase from '../../IaiLitBase.mjs';
import IaiResponseFilters from '../IaiResponseFilters/iai-response-filters.lit.csr.mjs';
import IaiTextInput from '../inputs/IaiTextInput/iai-text-input.lit.csr.mjs';
import IaiCheckboxInput from '../inputs/IaiCheckboxInput/iai-checkbox-input.lit.csr.mjs';
import IaiResponseFilterGroup from '../IaiResponseFilterGroup/iai-response-filter-group.lit.csr.mjs';
import IaiPageTitle from '../IaiPageTitle/iai-page-title.lit.csr.mjs';
import IaiDataTable from '../IaiDataTable/iai-data-table.lit.csr.mjs';
import IaiCsvDownload from '../IaiCsvDownload/iai-csv-download.lit.csr.mjs';
import IaiProgressBar from '../IaiProgressBar/iai-progress-bar.lit.csr.mjs';
import IaiAnimatedNumber from '../IaiAnimatedNumber/iai-animated-number.lit.csr.mjs';
import IaiExpandingPill from '../IaiExpandingPill/iai-expanding-pill.lit.csr.mjs';
import IaiChip from '../IaiChip/iai-chip.lit.csr.mjs';
import IaiExpandingText from '../IaiExpandingText/iai-expanding-text.lit.csr.mjs';
import IaiLoadingIndicator from '../IaiLoadingIndicator/iai-loading-indicator.lit.csr.mjs';
import IaiVirtualList from '../IaiVirtualList/iai-virtual-list.lit.csr.mjs';


export default class IaiResponseDashboard extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,

        consultationTitle: { type: String },
        consultationSlug: { type: String },
        questionTitle: { type: String },
        questionText: { type: String },
        questionSlug: { type: String },
        stanceOptions: { type: Array },
        themeMappings: { type: Array },
        demographicOptions: { type: Object },  // e.g. {"individual": ["true", "false"], "region": ["north", "south"]}
        responses: { type: Array },
        responsesTotal: { type: Number },
        free_text_question_part: { type: Boolean },
        has_multiple_choice_question_part: { type: Boolean },
        multiple_choice_summary: { type: Array },
        fetchData: { type: Function },

        _isLoading: { type: Boolean },
        _searchValue: { type: String },
        _themeSearchValue: { type: String },
        _demographicFilters: { type: Object },  // Changed from Array to Object to store filters by field
        _themeFilters: { type: Array },
        _themesPanelVisible: { type: Boolean },
        _stanceFilters: { type: Array },
        _responsesFilteredTotal: { type: Number },
        _evidenceRichFilters: { type: Array },
        _numberAnimationDuration: { type: Number },
        _searchDebounceTimer: { type: Number },
        _currentPage: { type: Number },
        _hasMorePages: { type: Boolean },
        _errorOccured: { type: Boolean },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-response-dashboard {
                margin-bottom: 5em;
            }
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
                display: flex;
                flex-direction: column;
                background: white;
                padding: 1em 2em;
                width: 73.5%;
            }
            iai-response-dashboard .responses-column .title-container {
                display: flex;
                justify-content:space-between;
                align-items: center;
                row-gap: 1em;
                padding-block: 1em;
                flex-wrap: wrap;
            }
            iai-response-dashboard .responses-column .title-container>*:first-child,
            iai-response-dashboard .responses-column .title-container>*:last-child {
                flex-grow: 1;
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
            iai-response-dashboard .table-title.themes-mentions {
                margin-bottom: 0;
            }
            iai-response-dashboard .themes-mentions iai-csv-download a {
                margin-bottom: 0;
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
            iai-response-dashboard thead tr {
                color: var(--iai-colour-text-secondary);
            }
            iai-response-dashboard table iai-expanding-pill button {
                display: flex;
                justify-content: space-between;
                width: 100%;
                font-size: 1.2em;
                color: black;
                background: var(--iai-colour-pink-transparent-mid);
            }
            iai-response-dashboard table iai-expanding-pill .body {
                font-size: 1.2em;
                transition-property: margin, padding, max-height;
            }
            iai-response-dashboard table iai-expanding-pill .body:not(.expanded) {
                margin: 0;
            }
            iai-response-dashboard table .percentage-cell {
                display: flex;
                gap: 0.2em;
                min-width: 4.5em;
                font-size: 2em;
                font-weight: bold;
                color: var(--iai-colour-text-secondary);
            }
            iai-response-dashboard table .total-count-cell {
                min-width: 10em;
            }
            iai-response-dashboard .title-container {
                display: flex;
                align-items: center;
                row-gap: 0;
                column-gap: 2em;
                flex-wrap: wrap;
            }
            iai-response-dashboard .ternary-button {
                background: none;
                border: none;
                border-radius: var(--iai-border-radius);
                cursor: pointer;
                transition: color 0.3s ease-in-out;
                padding: 0;
                text-align: start;
            }
            iai-response-dashboard .ternary-button:hover {
                color: var(--iai-colour-pink);
            }
            iai-response-dashboard .responses-row {
                display: flex;
                min-height: 90vh;
            }
            iai-response-dashboard .flex-grow {
                flex-grow: 1;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        this._PAGE_SIZE = 50;
        this._DEBOUNCE_DELAY = 500;
        this._currentFetchController = null;

        // Prop defaults
        this._isLoading = true;
        this._searchValue = "";
        this._themeSearchValue = "";
        this._stanceFilters = [];
        this._evidenceRichFilters = [];
        this._themeFilters = [];
        this._themesPanelVisible = false;
        this._demographicFilters = {};
        this._numberAnimationDuration = 500;
        this._searchDebounceTimer = null;
        this._currentPage = 1;
        this._hasMorePages = true;
        this._errorOccured = false;

        this.questionTitle = "";
        this.questionText = "";
        this.questionSlug = "";
        this.consultationTitle = "";
        this.consultationSlug = "";
        this.responses = [];
        this.responsesTotal = 0;
        this.themeMappings = [];
        this.stanceOptions = [];
        this.demographicOptions = {};
        this.free_text_question_part = false;
        this.has_multiple_choice_question_part = false;
        this.multiple_choice_summary = [];
        this.fetchData = window.fetch.bind(window);

        this.applyStaticStyles("iai-response-dashboard", IaiResponseDashboard.styles);
    }

    firstUpdated() {
        window.addEventListener("mousedown", this.handleThemesPanelClose);
    }

    fetchResponses = async () => {
        clearTimeout(this._searchDebounceTimer);

        this._searchDebounceTimer = setTimeout(async () => {
            if (!this._hasMorePages) {
                return;
            }

            if (this._currentFetchController) {
                console.log("aborting stale request");
                this._currentFetchController.abort();
            }

            const controller = new AbortController();
            const signal = controller.signal;
            this._currentFetchController = controller;

            this._errorOccured = false;
            this._isLoading = true;

            // Use multiple modular endpoints instead of single question_responses_json
            try {
                const [filteredResponsesData, themeAggregationsData, themeInformationData, demographicOptionsData] = await Promise.all([
                    // Get paginated response data
                    this.fetchData(`/consultations/${this.consultationSlug}/responses/${this.questionSlug}/filtered_responses?` + this.buildQuery(), { signal }).then(r => r.json()),
                    // Get theme aggregations (only on first page)
                    this._currentPage === 1 ? this.fetchData(`/api/consultations/${this.consultationSlug}/questions/${this.questionSlug}/theme-aggregations/?` + this.buildQuery(), { signal }).then(r => r.json()) : null,
                    // Get theme information (only on first page)
                    this._currentPage === 1 ? this.fetchData(`/api/consultations/${this.consultationSlug}/questions/${this.questionSlug}/theme-information/`, { signal }).then(r => r.json()) : null,
                    // Get demographic options (only on first page)
                    this._currentPage === 1 ? this.fetchData(`/api/consultations/${this.consultationSlug}/questions/${this.questionSlug}/demographic-options/`, { signal }).then(r => r.json()) : null
                ]);

                this.responses = this.responses.concat(
                    filteredResponsesData.all_respondents.map(response => ({
                        ...response,
                        visible: true,
                    }))
                );
                this.responsesTotal = filteredResponsesData.respondents_total;
                this._responsesFilteredTotal = filteredResponsesData.filtered_total;
                this._hasMorePages = filteredResponsesData.has_more_pages;

                // Update theme mappings only on first page to reflect current filters
                if (this._currentPage === 1 && themeAggregationsData && themeInformationData) {
                    // Create theme info lookup map
                    const themeInfoMap = themeInformationData.themes.reduce((map, theme) => {
                        map[theme.id] = theme;
                        return map;
                    }, {});
                    
                    // Convert theme_aggregations format to theme_mappings format
                    this.themeMappings = Object.entries(themeAggregationsData.theme_aggregations).map(([id, count]) => {
                        const themeInfo = themeInfoMap[id] || {};
                        return {
                            value: id,
                            label: themeInfo.name || "",
                            description: themeInfo.description || "",
                            count: count.toString()
                        };
                    });
                }

                // Update demographic options if available
                if (demographicOptionsData) {
                    this.demographicOptions = demographicOptionsData.demographic_options;
                }

            } catch (err) {
                if (err.name == "AbortError") {
                    console.log("stale request aborted");
                    return;
                } else {
                    console.error(err);
                    this._errorOccured = true;
                    return;
                }
            } finally {
                if (this._currentFetchController === controller) {
                    this._currentFetchController = null;
                }
                this._isLoading = false;
            }

            this._currentPage = this._currentPage + 1;
        }, this._DEBOUNCE_DELAY);
    }

    resetResponses = () => {
        this.responses = [];
        this._currentPage = 1;
        this._hasMorePages = true;
        this._isLoading = true;
    }

    updated(changedProps) {
        if (
            changedProps.has("_stanceFilters") ||
            changedProps.has("_evidenceRichFilters") ||
            changedProps.has("_searchValue")  ||
            changedProps.has("_themeFilters") ||
            changedProps.has("_demographicFilters")
        ) {
            this.resetResponses();
            this.fetchResponses();
            // this.applyFilters();
        }
    }

    disconnectedCallback() {
        window.removeEventListener("mousedown", this.handleThemesPanelClose);
    }

    handleSearchInput = (e) => {
        this._searchValue = e.target.value.trim();
    }
    handleStanceChange = (e) => {
        this._stanceFilters = this.addOrRemoveFilter(this._stanceFilters, e.target.value);
    }
    handleEvidenceRichChange = (e) => {
        this._evidenceRichFilters = this.addOrRemoveFilter(this._evidenceRichFilters, e.target.value);
    }
    handleThemeFilterChange = (e) => {
        this._themeFilters = this.addOrRemoveFilter(this._themeFilters, e.target.value);
    }
    handleDemographicChange = (field, value) => {
        if (!this._demographicFilters[field]) {
            this._demographicFilters[field] = [];
        }

        const currentValues = this._demographicFilters[field];
        const valueIndex = currentValues.indexOf(value);

        if (valueIndex > -1) {
            // Remove the value
            currentValues.splice(valueIndex, 1);
            if (currentValues.length === 0) {
                delete this._demographicFilters[field];
            }
        } else {
            // Add the value
            currentValues.push(value);
        }

        // Trigger reactive update
        this._demographicFilters = { ...this._demographicFilters };
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
            !(typeof response.identifier === "string" && response.identifier.toLocaleLowerCase().includes(this._searchValue.toLocaleLowerCase())) &&
            !response.multiple_choice_answer.join(",").toLocaleLowerCase().includes(this._searchValue.toLocaleLowerCase())
        ) {
            visible = false;
        }

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

        // filter by evidence rich
        if (this._evidenceRichFilters.length > 0) {
            if (
                this._evidenceRichFilters.includes("evidence-rich") &&
                !response.evidenceRich
            ) {
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

    buildQuery = () => {
        // conditionally add filters as query params
        const params = new URLSearchParams({
            ...(this._searchValue && {
                searchValue: this._searchValue
            }),
            ...(this._stanceFilters.length > 0 && {
                sentimentFilters: this._stanceFilters.join(",")
            }),
            ...(this._themeFilters.length > 0 && {
                themeFilters: this._themeFilters.join(",")
            }),
            ...(this._evidenceRichFilters.length > 0 && {
                evidenceRichFilter: this._evidenceRichFilters.join(",")
            }),
            page: this._currentPage,
            page_size: this._PAGE_SIZE.toString(),
        })

        // Add demographic filters using square bracket notation
        Object.entries(this._demographicFilters).forEach(([field, values]) => {
            if (values.length > 0) {
                params.append(`demographicFilters[${field}]`, values.join(","));
            }
        });

        return params.toString();
    }

    getPercentage = (partialValue, totalValue) => {
        if (totalValue === 0) {
            return 0;
        }
        return Math.round(((partialValue / totalValue) * 100));
    }

    formatFieldName = (field) => {
        // Convert field name to Title Case and handle special cases
        return field
            .replace(/_/g, ' ')
            .replace(/\b\w/g, l => l.toUpperCase());
    }

    formatDemographicValue = (field, value) => {
        // Special formatting for boolean values
        if (value === "true" || value === "false") {
            return value === "true" ? "Yes" : "No";
        }
        // Capitalize first letter for other values
        return value.charAt(0).toUpperCase() + value.slice(1);
    }

    getResponsesMessage = () => {
        if (this._errorOccured) {
            return "Something went wrong";
        }
        if (this.responses.length === 0 && !this._isLoading) {
            return "No matching responses found";
        }
        return "";
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
                                    <strong>${this.responsesTotal}</strong> responses
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

                                <div class="table-title themes-mentions">
                                    <div class="title-container">
                                        <h2 class="govuk-heading-m">
                                            Themes
                                        </h2>

                                        <button
                                            class="ternary-button"
                                            @click=${() => {
                                                const pills = Array.from(this.querySelectorAll("table iai-expanding-pill"));

                                                if (pills.filter(pill => !pill._expanded).length == 0) {
                                                    // If all pills are extended, collapse them all
                                                    pills.forEach(pill => pill._expanded = false);
                                                } else {
                                                    // else expand them all
                                                    pills.forEach(pill => pill._expanded = true);
                                                }
                                            }}
                                        >
                                            Hide/show all descriptions
                                        </button>
                                    </div>

                                    <iai-csv-download
                                        fileName="theme_mentions.csv"
                                        .data=${this.themeMappings
                                            .map(themeMapping => (
                                                {
                                                    "Theme name": themeMapping.label,
                                                    "Theme description": themeMapping.description,
                                                    "Total mentions": themeMapping.count,
                                                }
                                            ))
                                        }
                                    ></iai-csv-download>
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
                                    .initialSorts=${[
                                        {
                                            field: "Number of responses",
                                            ascending: false,
                                        }
                                    ]}
                                    .data=${this.themeMappings
                                        .map(themeMapping => (
                                            {
                                                // _sortValues are the values used for sorting comparison
                                                // instead of the actual value of a cell, which can be an obj etc.
                                                // particularly useful for html elements and dates.
                                                "_sortValues": {
                                                    "Theme name and description": themeMapping.label,
                                                    "Number of responses": parseInt(themeMapping.count),
                                                    "Percentage of responses": this.getPercentage(parseInt(themeMapping.count), this.responsesTotal),
                                                },
                                                "Theme name and description": html`
                                                    <iai-expanding-pill
                                                        .label=${themeMapping.label}
                                                        .body=${themeMapping.description}
                                                        .initialExpanded=${true}
                                                    ></iai-expanding-pill>
                                                `,
                                                "Percentage of responses": html`
                                                    <div class="percentage-cell">
                                                        <iai-animated-number
                                                            .number=${this.getPercentage(
                                                                parseInt(themeMapping.count),
                                                                this.responsesTotal
                                                            )}
                                                            .duration=${this._numberAnimationDuration}
                                                        ></iai-animated-number>
                                                        %
                                                    <div>
                                                `,
                                                "Number of responses": html`
                                                    <div class="total-count-cell">
                                                        <iai-progress-bar
                                                            .value=${this.getPercentage(parseInt(themeMapping.count), this.responsesTotal)}
                                                            .label=${themeMapping.count}
                                                        ></iai-progress-bar>
                                                    </div>
                                                `
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
                                        "_sortValues": {
                                            "Count": parseInt(Object.values(item)[0]),
                                        },
                                        "Answer": Object.keys(item)[0],
                                        "Count": Object.values(item)[0],
                                    }))}
                                ></iai-data-table>
                            </div>
                        </div>
                    </div>
                `
                : ""
            }

            <div class="govuk-grid-row govuk-!-margin-top-5 responses-row">
                <div class="govuk-grid-column-one-quarter-from-desktop filters-column">
                    <iai-response-filters>
                        <form slot="filters" method="GET">
                            <div class="iai-filter__options">

                                ${this.free_text_question_part
                                    ? html`
                                        <iai-response-filter-group title="Themes">
                                            <div slot="content" class="govuk-checkboxes govuk-checkboxes--small">
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
                                                        : ""
                                                    }
                                                </div>
                                            </div>
                                        </iai-response-filter-group>

                                        <hr />
                                    `
                                    : ""
                                }

                                ${this.demographicOptions && Object.keys(this.demographicOptions).length > 0 ?
                                    Object.entries(this.demographicOptions).map(([field, values]) => html`
                                        <iai-response-filter-group title="${this.formatFieldName(field)}">
                                            <div
                                                slot="content"
                                                class="govuk-checkboxes govuk-checkboxes--small"
                                                data-module="govuk-checkboxes"
                                                data-govuk-checkboxes-init=""
                                            >
                                                ${values.map((value, index) => html`
                                                    <iai-checkbox-input
                                                        name="demographic-filter-${field}"
                                                        inputId="demographic-${field}-${index}"
                                                        label="${this.formatDemographicValue(field, value)}"
                                                        value="${value}"
                                                        .handleChange=${() => this.handleDemographicChange(field, value)}
                                                    ></iai-checkbox-input>
                                                `)}
                                            </div>
                                        </iai-response-filter-group>
                                        <hr />
                                    `)
                                : ""}


                                <iai-response-filter-group title="Response sentiment">
                                    <div slot="content" class="govuk-checkboxes govuk-checkboxes--small">
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
                                    <div slot="content" class="govuk-checkboxes govuk-checkboxes--small">
                                        <iai-checkbox-input
                                            name="evidence-rich"
                                            inputId="show-evidence-rich"
                                            label="Only show evidence-rich"
                                            value="evidence-rich"
                                            .handleChange=${this.handleEvidenceRichChange}
                                        ></iai-checkbox-input>
                                    </div>
                                </iai-response-filter-group>
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
                            ${this._isLoading
                                ? html`<strong>Loading</strong> responses`
                                : html`Viewing <strong>${this._responsesFilteredTotal}</strong> responses`
                            }
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

                    <iai-virtual-list
                        class="flex-grow"
                        .data=${this._isLoading && this.responses.length === 0
                            ? [...Array(10).keys()].map(i => ({
                                id: "skeleton-response",
                                identifier: "skeleton-response",
                                free_text_answer_text: "Skeleton Body".repeat(50),
                                has_multiple_choice_question_part: false,
                                skeleton: true,
                              }))
                            : visibleResponses
                        }
                        .renderItem=${(response, index) => html`
                            <iai-response
                                class=${index === this.responses.length - 1 ? "last-item" : ""}
                                role="listitem"
                                .id=${response.inputId}
                                .identifier=${response.identifier}
                                .sentiment_position=${response.sentiment_position}
                                .free_text_answer_text=${response.free_text_answer_text}
                                .demographic_data=${response.demographic_data}
                                .themes=${response.themes}
                                .has_multiple_choice_question_part=${
                                response.hasOwnProperty("has_multiple_choice_question_part")
                                    ? response.has_multiple_choice_question_part
                                    : this.has_multiple_choice_question_part
                                }
                                .multiple_choice_answer=${response.multiple_choice_answer}
                                .searchValue=${this._searchValue}
                                .evidenceRich=${response.evidenceRich}
                                .skeleton=${response.skeleton}
                            ></iai-response>
                        `}
                        .handleScrollEnd=${() => {
                            if (this._isLoading) {
                                return;
                            }
                            this.fetchResponses();
                        }}
                        .isLoading=${this._isLoading}
                        .message=${this.getResponsesMessage()}
                    ></iai-virtual-list>

                    ${this._isLoading
                        ? html`<iai-loading-indicator></iai-loading-indicator>`
                        : ""
                    }
                </div>
            </div>
        `;
    }
}
customElements.define("iai-response-dashboard", IaiResponseDashboard);
