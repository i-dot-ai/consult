import { html, css } from 'lit';

import IaiLitBase from '../../../IaiLitBase.mjs';
import IaiQuestionOverview from '../IaiQuestionOverview/iai-question-overview.lit.csr.mjs';
import IaiQuestionTile from '../IaiQuestionTile/iai-question-tile.lit.csr.mjs';


export default class IaiQuestionTiles extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        questions: { type: Array },
        _selectedQuestion: { type: Object },
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
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.questions = [];
        this._selectedQuestion = null;

        this.applyStaticStyles("iai-question-tiles", IaiQuestionTiles.styles);
    }

    render() {
        return html`
            <div class="govuk-grid-row govuk-!-margin-top-5">
                <div class="govuk-grid-column-three-quarters-from-desktop tile-panel">
                    <div class="questions">
                        ${this.questions.map(question => html`
                            <iai-question-tile
                                .title=${question.title}
                                .body=${question.body}
                                @click=${_ => this._selectedQuestion = question}
                            ></iai-question-tile>
                        `)}
                    </div>
                </div>

                <div class="govuk-grid-column-one-quarter-from-desktop overview-panel">
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