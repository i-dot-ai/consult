import { html, css } from 'lit';

import IaiLitBase from '../../../IaiLitBase.mjs';
import IaiQuestionOverview from '../IaiQuestionOverview/iai-question-overview.lit.csr.mjs';
import IaiQuestionTile from '../IaiQuestionTile/iai-question-tile.lit.csr.mjs';
import IaiTextInput from '../../filters/IaiTextInput/iai-text-input.lit.csr.mjs';


export default class IaiQuestionTiles extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        questions: { type: Array },
        _visibleQuestions: { type: Array },
        _selectedQuestion: { type: Object },
        _searchValue: { type: String },
    }

    static styles = [
        IaiLitBase.styles,
        css`
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
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.questions = [];
        this._visibleQuestions = [];
        this._selectedQuestion = null;
        this._searchValue = "";

        this.applyStaticStyles("iai-question-tiles", IaiQuestionTiles.styles);
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

    render() {
        return html`
            <div class="govuk-grid-row govuk-!-margin-top-5">
                <div class="govuk-grid-column-three-quarters-from-desktop tile-panel">
                    <div class="questions">
                        ${this._visibleQuestions.length > 0
                            ? this._visibleQuestions.map(question => html`
                                <iai-question-tile
                                    .title=${question.title}
                                    .body=${question.body}
                                    .highlighted=${this._selectedQuestion == question}
                                    @click=${_ => this._selectedQuestion = question}
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
                            label="Search"
                            placeholder=${"Search..."}
                            value=${this._searchValue}
                            .handleInput=${(e) => this._searchValue = e.target.value}
                            .hideLabel=${true}
                        ></iai-text-input>
                    </div>
                    
                    ${this._selectedQuestion ? html`
                        <iai-question-overview
                            .title=${this._selectedQuestion.title}
                            .body=${this._selectedQuestion.body}
                            .handleClose=${() => this._selectedQuestion = null}
                        ></iai-question-overview>
                    ` : ""}
                </div>
            </div>
        `;
    }
}
customElements.define("iai-question-tiles", IaiQuestionTiles);