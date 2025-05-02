
       


import { html, css } from 'lit';
import IaiLitBase from '../../IaiLitBase.mjs';
import { unsafeHTML } from 'lit/directives/unsafe-html.js';


export default class IaiResponse extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        identifier: {type: String},
        individual: {type: String},
        free_text_answer_text: {type: String},
        themes: {type: Array}, // theme.stance, theme.name, theme.description
        sentiment_position: {type: String},
        demographic_data: {type: String}, // ?
        has_multiple_choice_question_part: {type: Boolean},
        multiple_choice_answer: {type: Array},
        searchValue: {type: String},
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-response {
                width: 100%;
            }

            iai-response .highlighted {
                background-color: yellow;
            }

            iai-response .sentiment-position {
                display: flex;
                align-items: center;
                gap: 0.6%;
            }

            iai-response .sentiment-position img {
                width: 24px;
                height: 24px;
            }
            
            iai-response .answer,
            iai-response .answer {
                line-height: 2em;
            }

            iai-response .themes {
                display: flex;
                align-items: center;
                gap: 0.6%;
            }
            iai-response .themes tool-tip,
            iai-response .themes tool-tip .iai-tooltip__button img {
                width: 14px;
            }
            iai-response .themes tool-tip .iai-tooltip__button {
                gap: 0.5em;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.identifier = "";
        this.individual = "";
        this.free_text_answer_text = "";
        this.themes = [];
        this.sentiment_position = "";
        this.demographic_data = "";
        this.has_multiple_choice_question_part = false;
        this.multiple_choice_answer = [];
        this.searchValue = "";

        this.applyStaticStyles("iai-response", IaiResponse.styles);
    }

    renderSentimentIcon = () => {
        const url = "https://consult.ai.cabinetoffice.gov.uk/static/icons/";

        if (this.sentiment_position == "AGREEMENT") {
            return html`<img src="${url + "thumbs-up.svg"}" alt="icon" />`;
        }
        if (this.sentiment_position == "DISAGREEMENT") {
            return html`<img src="${url + "thumbs-down.svg"}" alt="icon" />`;
        }
        return html`<img src="${url + "thumbs-up-down.svg"}" alt="icon" />`;
    }

    getFormattedSentiment = () => {
        return (
            this.sentiment_position.charAt(0).toLocaleUpperCase()
            + this.sentiment_position.slice(1).toLocaleLowerCase()
        );
    }

    getFreeTextAnswerText = () => {
        return unsafeHTML(this.free_text_answer_text.replace(
            this.searchValue,
            `<span class="highlighted">${this.searchValue}</span>`
        ));
    }

    render() {
        return html`
            <div class="iai-panel response govuk-!-margin-bottom-4">
                <div class="govuk-grid-row">
                    <div class="govuk-grid-column-two-thirds">
                        ${this.individual
                            ? html`<span class="govuk-caption-m">${this.individual}</span>`
                            : ""
                        }
                        <h2 class="govuk-heading-m">
                            Respondent ${this.identifier}
                        </h2>
                    </div>
                    
                    <!-- TODO: add pin here -->
                    <!--
                    <div class="govuk-grid-column-one-third">
                        <a class="pin-response align-right">
                            <p class="govuk-body-s govuk-!-margin-bottom-0 display-flex align-items-center">
                                <img src="/public/images/pin-response.svg" alt="Pin response">
                                <span>Pin response</span>
                            </p>
                        </a>
                    </div> -->
                </div>

                ${this.free_text_answer_text
                    ? html`
                        <h3 class="govuk-heading-s govuk-!-margin-bottom-4">
                            Free text response
                        </h3>
                        ${this.sentiment_position
                            ? html`
                                <p class="govuk-body sentiment-position">
                                    ${this.renderSentimentIcon()}
                                    <span>
                                        ${this.getFormattedSentiment()}
                                    </span>
                                </p>
                            `
                            : ""
                        }

                        ${this.themes.map(theme => html`
                            <div class="govuk-pill-container themes">
                                <div class="govuk-pill">
                                    <tool-tip class="iai-tooltip">
                                        <div class="iai-tooltip__button" role="tooltip" tabindex="0" aria-describedby="tooltip-content-${theme.id}">
                                            <span>${theme.name}</span>
                                            <img src="https://consult.ai.cabinetoffice.gov.uk/static/icons/question-mark.svg" alt="info"/>
                                        </div>
                                        <div class="iai-tooltip__content" id="tooltip-content-${theme.id}">
                                            ${theme.description}
                                        </div>
                                    </tool-tip>
                                </div>
                            </div>
                        `)}

                        <p class="govuk-body answer">
                            ${this.getFreeTextAnswerText()}
                        </p>
                    `
                    : ""
                }

                ${this.has_multiple_choice_question_part
                    ? html`
                        <h3 class="govuk-heading-s govuk-!-margin-bottom-2">
                            Response to multiple choice
                        </h3>
                        <p class="govuk-body answer">
                            ${this.multiple_choice_answer.length > 0
                                ? this.multiple_choice_answer.join(", ")
                                : "Not answered"}
                        </p>
                    `
                    : ""
                }

                ${this.demographic_data
                    ? html`
                        <p class="govuk-body-s">
                            ${this.demographic_data}
                        </p>`
                    : ""
                }
            </div>
        `;
    }
}
customElements.define("iai-response", IaiResponse);