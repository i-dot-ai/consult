import { html, css } from 'lit';

import IaiLitBase from '../../../IaiLitBase.mjs';
import IaiQuestionOverview from '../IaiQuestionOverview/iai-question-overview.lit.csr.mjs';
import IaiQuestionTile from '../IaiQuestionTile/iai-question-tile.lit.csr.mjs';
import IaiTextInput from '../../inputs/IaiTextInput/iai-text-input.lit.csr.mjs';


export default class IaiQuestionTiles extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        consultationName: { type: String },
        questions: { type: Array },
        _visibleQuestions: { type: Array },
        _selectedQuestion: { type: Object },
        _searchValue: { type: String },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-question-tiles iai-icon .material-symbols-outlined {
                font-size: 2em;
            }
            iai-question-tiles .questions {
                display: flex;
                flex-wrap: wrap;
                gap: 1em;
            }
            iai-question-tiles .tile-panel {
                padding-right: 0;
            }
            iai-question-tiles .overview-panel {
                padding-left: 0;
            }
            iai-question-tiles .search-container {
                margin-bottom: 1em;
            }
            iai-question-tiles .search-container label {
                display: flex;
                align-items: center;
                margin-bottom: 0.5em;
                font-weight: normal;
                font-size: 1em;
                line-height: 0;
            }
            iai-question-tiles .search-container label iai-icon {
                margin-right: 0.5em;
            }
            iai-question-tiles .questions {
                max-height: 80vh;
                overflow: auto;
            }
            @media only screen and (max-width: 770px) {
                iai-question-tiles .overview-panel {
                    padding: 1em;
                    padding-top: 2em;
                }
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.consultationName = "";
        this.questions = [];
        this._visibleQuestions = [];
        this._selectedQuestion = null;
        this._searchValue = "";

        this.applyStaticStyles("iai-question-tiles", IaiQuestionTiles.styles);
    }

    firstUpdated() {
        if (this.questions.length > 0) {
            this._selectedQuestion = this.questions[0];
        }
    }

    updated(changedProps) {
        if (changedProps.has("_searchValue")) {
            this._visibleQuestions = this.questions.filter(
                question => this.searchMatches(question)
            );
        }
    }

    searchMatches = (question) => {
        if (!this._searchValue) {
            return true;
        }
        return (
            question.title.toLocaleLowerCase().includes(this._searchValue.toLocaleLowerCase()) ||
            question.body.toLocaleLowerCase().includes(this._searchValue.toLocaleLowerCase())
        )
    }

    handleViewClick = (e, question) => {
        e.stopPropagation();

        this._selectedQuestion = question;
    }

    handleTileClick = (e, url) => {
        window.location.href = url;
    }

    render() {
        return html`
            <iai-page-title
                title="All Questions"
                .subtitle=${this.consultationName}
            ></iai-page-title>

            <div class="govuk-grid-row govuk-!-margin-top-5">
                <div class="govuk-grid-column-three-quarters-from-desktop tile-panel">
                    <div class="questions">
                        ${this._visibleQuestions.length > 0
                            ? this._visibleQuestions.map(question => html`
                                <iai-question-tile
                                    .questionId=${question.id}
                                    .title=${question.title}
                                    .body=${question.body}
                                    .highlighted=${this._selectedQuestion == question}
                                    .searchValue=${this._searchValue}
                                    .handleViewClick=${(e) => this.handleViewClick(e, question)}
                                    .handleBodyClick=${(e) => this.handleTileClick(e, question.url)}
                                ></iai-question-tile>
                            `)
                            : html`<p>No matching question found.</p>`
                        }
                    </div>
                </div>

                <div class="govuk-grid-column-one-quarter-from-desktop overview-panel">
                    <div class="search-container">
                        <iai-text-input
                            inputId="question-search"  
                            name="question-search"
                            .label=${html`
                                <iai-icon
                                    slot="icon"
                                    name="search"
                                    .color=${"var(--iai-colour-text-secondary)"}
                                    .fill=${0}
                                ></iai-icon>
                                Search
                            `}
                            placeholder=${"Search..."}
                            value=${this._searchValue}
                            .handleInput=${(e) => this._searchValue = e.target.value}
                            .hideLabel=${false}
                        ></iai-text-input>
                    </div>
                    
                    ${this._selectedQuestion ? html`
                        <iai-question-overview
                            .title=${this._selectedQuestion.title}
                            .body=${this._selectedQuestion.body}
                            .responses=${this._selectedQuestion.responses}
                            .multiResponses=${this._selectedQuestion.multiResponses}
                            .handleClose=${() => this._selectedQuestion = null}
                        ></iai-question-overview>
                    ` : ""}
                </div>
            </div>
        `;
    }
}
customElements.define("iai-question-tiles", IaiQuestionTiles);