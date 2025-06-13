import { html, css } from 'lit';

import IaiLitBase from '../../IaiLitBase.mjs';
import IaiExpandingText from '../IaiExpandingText/iai-expanding-text.lit.csr.mjs';
import IaiExpandingPill from '../IaiExpandingPill/iai-expanding-pill.lit.csr.mjs';
import IaiIcon from '../IaiIcon/iai-icon.mjs';


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
        evidenceRich: {type: Boolean},
        skeleton: {type: Boolean},
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-response {
                width: 100%;
            }

            iai-response .matched-text {
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

            iai-response .themes tool-tip,
            iai-response .themes tool-tip .iai-tooltip__button img {
                width: 14px;
            }
            iai-response .themes tool-tip .iai-tooltip__button {
                gap: 0.5em;
            }
            iai-response iai-expanding-text .iai-text-content {
                transition: none;
            }
            iai-response .response {
                border: 2px solid var(--iai-colour-border-grey);
            }
            iai-response .themes {
                margin-bottom: 1em;
            }
            iai-response .space-between {
                display: flex;
                justify-content: space-between;
                width: 100%;
            }
            iai-response iai-icon .material-symbols-outlined {
                font-size: 2em;
            }
            iai-response .demographic-data ul {
                display: flex;
                flex-direction: column;
            }
            iai-response .skeleton {
                background: black;
                color: transparent;
                animation: fadeInOut 1s ease-in-out infinite alternate;
                user-select: none;
            }
            @keyframes fadeInOut {
                from {
                    opacity: 0.1;
                }
                to {
                    opacity: 0.2;
                }
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
        this.demographic_data = undefined;
        this.has_multiple_choice_question_part = false;
        this.multiple_choice_answer = [];
        this.searchValue = "";
        this.evidenceRich = false;
        this.skeleton = false;

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
        if (this.sentiment_position == "AGREEMENT") {
            return html`<strong>Agree</strong> with the question`;
        } else if (this.sentiment_position == "DISAGREEMENT") {
            return html`<strong>Disagree</strong> with the question`;
        } else if (this.sentiment_position == "UNCLEAR") {
            return html`<strong>Unclear</strong> about the question`;
        };
    }

    getHighlightedText = (fullText, matchedText) => {
        if (!matchedText) {
            return "";
        }
        const regex = new RegExp(matchedText, "gi");
        return fullText.replace(regex, match => `<span class="matched-text">${match}</span>`);
    }

    render() {
        return html`
            <div class="iai-panel response govuk-!-margin-bottom-4">
                <div class="govuk-grid-row">
                    <div class="govuk-grid-column-two-thirds space-between">
                        <h2 class=${"govuk-heading-m" + (this.skeleton ? " skeleton" : "")}>
                            Respondent ${this.identifier}
                        </h2>

                        ${this.evidenceRich
                            ? html`
                                <iai-icon
                                    title="Evidence-rich response"
                                    name="diamond"
                                    .opsz=${48}
                                ></iai-icon>
                            `
                            : ""
                        }
                    </div>
                </div>

                ${this.free_text_answer_text
                    ? html`
                        <p 
                            class=${"govuk-body answer" + (this.skeleton ? " skeleton" : "")}
                            data-testid="free-text-answer"
                        >
                            <iai-expanding-text
                                .text=${this.getHighlightedText(this.free_text_answer_text, this.searchValue)}    
                                .lines=${2}
                            ></iai-expanding-text>
                        </p>

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

                        <div class="themes">
                            ${Array.isArray(this.themes)
                                ? this.themes.map(theme => html`
                                    <iai-expanding-pill
                                        .label=${theme.name}
                                        .body=${theme.description}
                                        .initialExpanded=${false}
                                    ></iai-expanding-pill>
                                `)
                                : ""}
                        </div>
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
                                : "Not answered"
                            }
                        </p>
                    `
                    : ""
                }

                ${this.demographic_data && this.demographic_data.length > 0
                    ? html`
                        <div class="govuk-body-s demographic-data">
                            <h3>Demographic Data</h3>
                            <ul>
                                ${Object.keys(this.demographic_data).map(key => html`
                                    <li>
                                        ${key.slice(0, 1).toLocaleUpperCase()
                                            + key.slice(1)}: ${this.demographic_data[key]
                                        }
                                    </li>
                                `)}
                            </ul>
                        </div>
                    `
                    : ""
                }
            </div>
        `;
    }
}
customElements.define("iai-response", IaiResponse);