import { html, css } from 'lit';

import IaiLitBase from '../../../../IaiLitBase.mjs';
import Title from '../../Title/title.lit.csr.mjs';
import Panel from '../../Panel/panel.lit.csr.mjs';
import Button from '../../Button/button.lit.csr.mjs';
import IaiIcon from '../../../IaiIcon/iai-icon.mjs';


export default class QuestionTitle extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        status: { type: String },
        title: { type: String },
        description: { type: String },
        department: { type: String },
        numResponses: { type: Number },
        numQuestions: { type: Number },
        numThemes: { type: Number },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-silver-question-title {
                color: var(--iai-silver-color-text);
            }
            iai-silver-question-title .topbar {
                display: flex;
                justify-content: space-between;
                margin-bottom: 1em;
            }
            iai-silver-question-title .topbar .tags {
                display: flex;    
                align-items: center;
                gap: 0.5em;
            }

            iai-silver-question-title .tag {
                padding: 0.3em 0.5em;
            }

            iai-silver-question-title .status {
                display: flex;
                justify-content: center;
                align-items: center;
                font-size: 0.8em;
                color: white;
                background: #85d07e;                
                border-radius: 0.5em;
            }
            iai-silver-question-title .responses {
                font-weight: bold;
            }
            iai-silver-question-title .department {
                font-size: 0.8em;
            }

            iai-silver-question-title iai-silver-button button {
                padding: 0.3em;
                border: none;
                font-size: 1.5em;
            }
            iai-silver-question-title .details {
                display: flex;
                align-items: center;
                gap: 1em;
                flex-wrap: wrap;
                margin-top: 1em;
            }
            iai-silver-question-title .title-container {
                display: flex;
                justify-content:
                space-between; gap: 1em;
                line-height: 1.5em;
            }
            iai-silver-question-title [slot="content"] {
                padding-block: 0.5em;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.status = "";
        this.title = "";
        this.department = "";
        this.numResponses = 0;

        this.applyStaticStyles("iai-silver-question-title", QuestionTitle.styles);
    }

    getTagColor = (status) => {
        switch (status) {
            case this.CONSULTATION_STATUSES.open:
                return {
                    primary: "var(--iai-silver-color-teal)",
                    secondary: "var(--iai-silver-color-teal-light)",
                };
            case this.CONSULTATION_STATUSES.analysing:
                return {
                    primary: "var(--iai-silver-color-teal)",
                    secondary: "var(--iai-silver-color-teal-light)",
                };
            case this.CONSULTATION_STATUSES.completed:
                return {
                    primary: "var(--iai-silver-color-teal)",
                    secondary: "var(--iai-silver-color-teal-light)",
                };
            case this.CONSULTATION_STATUSES.closed:
                return {
                    primary: "var(--iai-silver-color-teal)",
                    secondary: "var(--iai-silver-color-teal-light)",
                };
        }
    }

    render() {
        return html`
            <style>
                #${this.contentId} .tag.status {
                    color: ${this.getTagColor(this.status).primary};
                    background: ${this.getTagColor(this.status).secondary};
                    border: 1px solid ${this.getTagColor(this.status).primary};
                }
            </style>
            <iai-silver-panel id=${this.contentId}>
                <div slot="content">
                    <div class="title-container">
                        <iai-silver-title
                            .text=${this.title}
                            .level=${2}
                        ></iai-silver-title>

                        <iai-silver-button
                            .text=${html`
                                <iai-icon
                                    .name=${"star"}
                                    .color=${"var(--iai-silver-color-text)"}
                                ></iai-icon>
                            `}
                            .handleClick=${() => console.log("button clicked")}
                        ></iai-silver-button>
                    </div>

                    <div class="details">
                        <small class="responses">
                            ${this.numResponses.toLocaleString()} responses
                        </small>

                        <span class="tag status">
                            ${this.status}
                        </span>

                        <small class="department">
                            ${this.department}
                        </small>
                    </div>
                </div>
            </iai-silver-panel>
        `
    }
}
customElements.define("iai-silver-question-title", QuestionTitle);