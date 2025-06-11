import { html, css } from 'lit';

import IaiLitBase from '../../../IaiLitBase.mjs';
import IaiQuestionTopbar from '../IaiQuestionTopbar/iai-question-topbar.lit.csr.mjs';
import IaiQuestionBody from '../IaiQuestionBody/iai-question-body.lit.csr.mjs';
import IaiIcon from '../../IaiIcon/iai-icon.mjs';
import IaiIconButton from '../IaiIconButton/iai-icon-button.lit.csr.mjs';
import IaiQuestionOverviewSubtitle from '../IaiQuestionOverviewSubtitle/iai-question-overview-subtitle.lit.csr.mjs';
import IaiTextResponseItem from '../IaiTextResponseItem/iai-text-response-item.lit.csr.mjs';
import IaiMultiResponseItem from '../IaiMultiResponseItem/iai-multi-response-item.lit.csr.mjs';


export default class IaiQuestionOverview extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        title: { type: String },
        body: { type: String },
        responses: { type: Object }, //  agreement | unclear | disagreement
        multiResponses: { type: Object },
        handleClose: { type: Function },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-question-overview .question-overview {
                background: white;
                padding: 1em;
                border-radius: var(--iai-border-radius);
            }
            iai-question-overview .multi-response-list {
                padding: 0;
                margin: 0;
                margin-top: 0.5em;
                list-style: none;
            }
            iai-question-overview .text-response-list {
                padding: 0;
                margin: 0;
                margin-top: 1em;
            }
            iai-question-overview hr {
                margin-block: 1em;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.title = "";
        this.body = "";
        this.responses = {};
        this.multiResponses = {};
        this.handleClose = () => {};
        
        this.applyStaticStyles("iai-question-overview", IaiQuestionOverview.styles);
    }

    getTextResponseTotal = () => {
        return (
            (this.responses.agreement || 0) +
            (this.responses.unclear || 0) +
            (this.responses.disagreement || 0)
        );
    }

    getMultiResponseTotal = () => {
        return Object.values(this.multiResponses).reduce((acc, curr) => acc + curr, 0);
    }

    render() {
        const textResponseTotal = this.getTextResponseTotal();
        const multiResponseTotal = this.getMultiResponseTotal();
        
        return html`
            <div class="question-overview">
                <iai-question-topbar .title=${this.title}>
                    <div slot="buttons">
                        <iai-icon-button
                            title="Close question overview"
                            .handleClick=${this.handleClose}
                        >
                            <iai-icon
                                slot="icon"
                                name="close"
                                .color=${"var(--iai-colour-text-secondary)"}
                            ></iai-icon>
                        </iai-icon-button>
                    </div>
                </iai-question-topbar>

                <iai-question-body
                    .text=${this.body}
                ></iai-question-body>

                <hr />

                <iai-question-overview-subtitle
                    title="Free Text Responses"
                    .total=${textResponseTotal}
                ></iai-question-overview-subtitle>
                
                ${!this.responses.agreement && !this.responses.disagreement && !this.responses.unclear
                    ? html`<p class="govuk-body">This question does not have free text responses</p>`
                    : html`
                        <ul class="text-response-list">
                            <iai-text-response-item
                                iconName="thumb_up"
                                .text=${html`<strong>${this.responses.agreement}</strong> responses <strong>agree</strong> with the question`}
                            ></iai-text-response-item>
                            <iai-text-response-item
                                iconName="thumbs_up_down"
                                .text=${html`<strong>${this.responses.unclear}</strong> responses are <strong>unclear</strong> on whether agree or disagree with the question`}
                            ></iai-text-response-item>
                            <iai-text-response-item
                                iconName="thumb_down"
                                .text=${html`<strong>${this.responses.disagreement}</strong> responses <strong>disagree</strong> with the question`}
                            ></iai-text-response-item>
                        </ul>
                    `
                }

                <hr />

                <iai-question-overview-subtitle
                    title="Multi-Choice Responses"
                    .total=${multiResponseTotal}
                ></iai-question-overview-subtitle>

                ${!this.multiResponses || !Object.keys(this.multiResponses).length > 0
                    ? html`<p class="govuk-body">This question does not have multiple choice responses</p>`
                    : html`
                        <ul class="multi-response-list">
                            ${Object.keys(this.multiResponses).map(key => html`
                                <iai-multi-response-item
                                    .countName=${key}
                                    .countValue=${this.multiResponses[key]}
                                    .totalCounts=${multiResponseTotal}
                                ></iai-multi-response-item>
                                
                            `)}
                        </ul>
                    `
                }
            </div>
        `;
    }
}
customElements.define("iai-question-overview", IaiQuestionOverview);