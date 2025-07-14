import { html, css } from 'lit';

import IaiLitBase from '../../../../IaiLitBase.mjs';
import Title from '../../Title/title.lit.csr.mjs';
import Panel from '../../Panel/panel.lit.csr.mjs';
import Card from '../../Card/card.lit.csr.mjs';
import Button from '../../Button/button.lit.csr.mjs';
import IaiIcon from '../../../IaiIcon/iai-icon.mjs';


import ThemeAnalysis from '../../ThemeAnalysis/theme-analysis.lit.csr.mjs';
import QuestionTitle from '../QuestionTitle/question-title.lit.csr.mjs';
import TabView from '../../../TabView/tab-view.lit.csr.mjs';
import CrossSearch from '../../CrossSearch/cross-search.lit.csr.mjs';
import DemographicsSection from '../DemographicsSection/demographics-section.lit.csr.mjs';
import Tag from '../../Tag/tag.lit.csr.mjs';
import ResponseRefinement from '../ResponseRefinement/response-refinement.lit.csr.mjs';
import ResponsesList from '../ResponsesList/responses-list.lit.csr.mjs';


export default class QuestionDetailPage extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,

        _activeTab: { type: String },
        _isLoading: { type: Boolean },
        _currentPage: { type: Number},
        _hasMorePages: { type: Boolean},
        _errorOccured: { type: Boolean},
        fetchData: { type: Function },
        _isFavourited: { type: Boolean},

        consultationSlug: { type: String },
        questionSlug: { type: String },
        consultationTitle: { type: String},
        questionText: { type: String},
        questionId: { type: String },

        responses: { type: Array },
        _responsesTotal: { type: Number },
        _filteredTotal: { type: Number },
        _themes: { type: Array },
        _demoData: { type: Object },

        _searchValue: { type: String },
        _searchMode: { type: String },
        _highlightMatches: { type: Boolean },
        _evidenceRichFilter: { type: Boolean },
        _themeFilters: { type: Array },
        _demoFilters: { type: Object },

        _themesSortType: { type: String },
        _themesSortDirection: { type: String },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-question-detail-page {
                color: var(--iai-silver-color-text);
            }
            iai-question-detail-page select,
            iai-question-detail-page input {
                width: 100%;
            }
            iai-question-detail-page section {
                margin-bottom: 1em;
            }
            iai-question-detail-page section.breadcrumbs {
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 1em;
            }
            iai-question-detail-page section.breadcrumbs iai-silver-button button {
                display: flex;
                gap: 0.5em;
                align-items: center;
                justify-content: space-between;
            }
            iai-question-detail-page .response-total {
                display: flex;
                align-items: center;
            }
            iai-question-detail-page iai-icon-button {
                margin-top: -0.4em;
            }
            iai-question-detail-page .load-more-button {
                margin-top: 1em;
                display: flex;
                justify-content: center;
            }
            @media screen and (max-width: 500px) {
                iai-question-detail-page section.breadcrumbs {
                    justify-content: center;
                }
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();
        
        this._MAX_THEME_FILTERS = 3;
        this._PAGE_SIZE = 50;
        this._DEBOUNCE_DELAY = 500;
        this._TAB_INDECES = {
            "Question Summary" : 0,
            "Response Analysis" : 1,
        };
        this._currentFetchController = null;

        // Prop defaults
        this._activeTab = this._TAB_INDECES["Question Summary"];
        this._isLoading = false;
        this._currentPage = 1;
        this._hasMorePages = true;
        this._errorOccured = false;
        this.fetchData = window.fetch.bind(window);
        this._isFavourited = false;

        this.consultationSlug = "";
        this.questionSlug = "";
        this.consultationTitle = "";
        this.questionText = "";
        this.questionId = "";

        this.responses = [];
        this._responsesTotal = 0;
        this._filteredTotal = 0;
        this._themes = [];
        this._demoData = {};
        
        this._searchValue = "";
        this._searchMode = "keyword";
        this._highlightMatches = true;
        this._evidenceRichFilter = false;
        this._themeFilters = [];
        this._demoFilters = {};

        this._themesSortType = "frequency"; // "frequency" | "alphabetical"
        this._themesSortDirection = "descending"; // "ascending" | "descending"

        this.applyStaticStyles("iai-question-detail-page", QuestionDetailPage.styles);
    }

    updateThemeFilters = (newFilter) => {
        if (!newFilter) {
            // Clear filters if newFilter is falsy
            this._themeFilters = [];
            return;
        }
        if (this._themeFilters.includes(newFilter)) {
            this._themeFilters = [...this._themeFilters.filter(filter => filter !== newFilter)];
        } else {
            if (this._themeFilters.length === this._MAX_THEME_FILTERS) {
                this._themeFilters = [...this._themeFilters.slice(1), newFilter];
            } else {
                this._themeFilters = [...this._themeFilters, newFilter];
            }
        }
    }

    buildQuery = () => {
        // conditionally add filters as query params
        const params = new URLSearchParams({
            ...(this._searchValue && {
                searchValue: this._searchValue
            }),
            ...(this._themeFilters.length > 0 && {
                themeFilters: this._themeFilters.join(",")
            }),
            ...(this._searchMode && {
                searchMode: this._searchMode
            }),
            ...(this._evidenceRichFilter && {
                evidenceRich: this._evidenceRichFilter
            }),
            // Add demofilters as string formatted as "foo:1,bar:2"
            ...(Object.values(this._demoFilters).filter(Boolean).length > 0 && {
                demoFilters: Object.keys(this._demoFilters)
                    .filter(Boolean)
                    .map(key => `${key}:${this._demoFilters[key]}`)
                    .join(",")
            }),
            ...(this._themesSortType && {
                themesSortType: this._themesSortType
            }),
            ...(this._themesSortDirection && {
                themesSortDirection: this._themesSortDirection
            }),
            page: this._currentPage,
            page_size: this._PAGE_SIZE.toString(),
        })

        return params.toString();
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

            const url = `/consultations/${this.consultationSlug}/responses/${this.questionSlug}/json?` + this.buildQuery();

            let response;
            try {
                response = await this.fetchData(url, { signal });
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

            if (!response.ok) {
                this._errorOccured = true;
                throw new Error(`Response status: ${response.status}`);
            }

            const responsesData = await response.json();

            this.responses = this.responses.concat(responsesData.all_respondents);

            this._responsesTotal = responsesData.respondents_total;
            this._filteredTotal = responsesData.filtered_total;

            this._themes = responsesData.theme_mappings.map(mapping => ({
                id: mapping.value,
                title: mapping.label,
                description: mapping.description,
                mentions: parseInt(mapping.count),
                handleClick: () => {
                    this._themeFilters = [mapping.value];
                    this._activeTab = this._TAB_INDECES["Response Analysis"];
                }
            }));

            this._demoData = responsesData.demographic_aggregations || {};

            // Update theme mappings only on first page (when _currentPage === 1) to reflect current filters
            if (this._currentPage === 1 && responsesData.theme_mappings) {
                this.themeMappings = responsesData.theme_mappings;
            }

            this._hasMorePages = responsesData.has_more_pages;

            this._currentPage = this._currentPage + 1;
        }, this._DEBOUNCE_DELAY);
    }

    resetResponses = () => {
        this.responses = [];
        this._currentPage = 1;
        this._hasMorePages = true;
        this._isLoading = true;
    }

    firstUpdated() {
        this._isFavourited = this.isFavourited();
    }

    updated(changedProps) {
        if (
            changedProps.has("_searchValue")        ||
            changedProps.has("_searchMode")         ||
            changedProps.has("_evidenceRichFilter") ||
            changedProps.has("_themeFilters")       ||
            changedProps.has("_demoFilters")        ||
            changedProps.has("_themesSortType")     ||
            changedProps.has("_themesSortDirection")
        ) {
            this.resetResponses();
            this.fetchResponses();
        }
    }

    isFavourited() {
        return this.getStoredValues(this._STORAGE_KEYS.FAVOURITE_QUESTIONS).includes(this.questionId);
    }

    renderThemeAnalysisSection = () => {
        return html`
            <section class="theme-analysis">
                <iai-theme-analysis
                    .demoData=${this._demoData}
                    .themes=${this._themes}

                    .themeFilters=${this._themeFilters}
                    .updateThemeFilters=${this.updateThemeFilters}
                    
                    .sortType=${this._themesSortType}
                    .setSortType=${newSortType => this._themesSortType = newSortType}

                    .sortDirection=${this._themesSortDirection}
                    .setSortDirection=${newSortDirection => this._themesSortDirection = newSortDirection}

                    .demoFilters=${this._demoFilters}
                    .setDemoFilters=${(newFilterKey, newFilterValue) => {
                        if (!newFilterKey || !newFilterValue) {
                            // Clear filters if nothing is passed
                            this._demoFilters = {};
                        }
                        this._demoFilters = {
                            ...this._demoFilters,
                            [newFilterKey]: newFilterValue
                        }
                    }}
                ></iai-theme-analysis>
            </section>
        `
    }

    renderResponsesSection = () => {
        return html`
            <section>
                <iai-response-refinement
                    .demoData=${this._demoData}
                    .themes=${this._themes}

                    .searchValue=${this._searchValue}
                    .setSearchValue=${newSearchValue => this._searchValue = newSearchValue}

                    .searchMode=${this._searchMode}
                    .setSearchMode=${newSearchMode => this._searchMode = newSearchMode}

                    .evidenceRich=${this._evidenceRichFilter}
                    .setEvidenceRich=${newEvidenceRich => this._evidenceRichFilter = newEvidenceRich}

                    .highlightMatches=${this._highlightMatches}
                    .setHighlightMatches=${newHighlightMatches => this._highlightMatches = newHighlightMatches}

                    .demoFilters=${this._demoFilters}
                    .setDemoFilters=${(newFilterKey, newFilterValue) => this._demoFilters = {
                        ...this._demoFilters,
                        [newFilterKey]: newFilterValue
                    }}

                    .themeFilters=${this._themeFilters}
                    .updateThemeFilters=${this.updateThemeFilters}
                ></iai-response-refinement>
            </section>

            <section>
                <iai-silver-responses-list
                    .responses=${
                        this.responses.map(response => ({
                            text: response.free_text_answer_text,
                            themes: response.themes.map(theme => ({
                                id: theme.id,
                                text: theme.description,
                            })),
                            evidenceRich: response.evidenceRich,
                            multiAnswers: response.multiple_choice_answer || [],
                            demoData: Object.values(response.demographic_data) || [],
                        }))
                    }
                    .handleScrollEnd=${() => {
                        // // Uncomment to enable infinite scroll
                        // if (this._isLoading) {
                        //     return;
                        // }
                        // this.fetchResponses();
                    }}
                    .responsesTotal=${this._responsesTotal}
                    .filteredTotal=${this._filteredTotal}
                    .isLoading=${this._isLoading}
                    .highlightedText=${this._highlightMatches ? this._searchValue : ""}
                    .handleThemeTagClick=${(themeId) => {
                        this.updateThemeFilters(themeId);
                        this._activeTab = this._TAB_INDECES["Question Summary"];
                    }}
                ></iai-silver-responses-list>

                ${this._hasMorePages ? html`
                    <iai-silver-button
                        class="load-more-button"
                        .text=${`Load more (${this._filteredTotal - this.responses.length} remaining)`}
                        .handleClick=${() => {
                            if (this._isLoading) {
                                return;
                            }
                            this.fetchResponses();
                        }}
                    ></iai-silver-button>`
                : ""}
            </section>
        `
    }

    renderTabButton = (text, icon) => {
        return html`
            <iai-icon
                .name=${icon}
            ></iai-icon>
            <span>
                ${text}
            </span>
        `
    }

    render() {
        return html`
            <section class="breadcrumbs">
                <iai-silver-button
                    .text=${html`
                        <iai-icon
                            .name=${"chevron_left"}
                            .color=${"var(--iai-silver-color-text)"}
                        ></iai-icon>
                        <span>Back to all questions</span>
                    `}
                    .handleClick=${() => window.location.href = `/consultations/${this.consultationSlug}/`}
                ></iai-silver-button>

                <small>
                    Choose a different question to analyse
                </small>
            </section>

            <section class="question-title">
                <iai-silver-cross-search-card
                    .type=${"question"}
                    .title=${this.questionText}
                    .aside=${html`
                        <iai-icon-button
                            class="favourite-button"
                            title="Favourite this question"
                            @click=${(e) => {
                                e.stopPropagation();
                                this.toggleStorage(
                                    this.questionId,
                                    this._STORAGE_KEYS.FAVOURITE_QUESTIONS
                                );
                                this._isFavourited = this.isFavourited();
                            }}
                        >
                            <iai-icon
                                slot="icon"
                                name="star"
                                .color=${"var(--iai-silver-color-text)"}
                                .fill=${this._isFavourited ? 1 : 0}
                            ></iai-icon>
                        </iai-icon-button>
                    `}
                    .footer=${html`
                        <small class="response-total">
                            ${this._responsesTotal.toLocaleString()} responses
                        </small>
                        <iai-silver-tag
                            .status=${"Open"}
                            .text=${"Open"}
                            .icon=${"chat_bubble"}
                        ></iai-silver-tag>
                    `}
                ></iai-silver-cross-search-card>
            </section>

            <section>
                <iai-demographics-section
                    .data=${this._demoData}
                    .themeFilters=${this._themeFilters}
                    .total=${this._filteredTotal}
                ></iai-demographics-section>
            </section>

            <iai-tab-view
                .activeTab=${this._activeTab}
                .handleTabChange=${(newTab) => this._activeTab = newTab}
                .tabs=${[
                    {
                        title: this.renderTabButton("Question summary", "lan"),
                        content: this.renderThemeAnalysisSection()
                    },
                    {
                        title: this.renderTabButton("Response analysis", "finance"),
                        content: this.renderResponsesSection()
                    },
                ]}
            ></iai-tab-view>
        `
    }
}
customElements.define("iai-question-detail-page", QuestionDetailPage);