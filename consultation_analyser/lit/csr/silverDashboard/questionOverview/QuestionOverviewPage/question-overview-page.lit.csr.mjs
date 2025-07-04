import { html, css } from 'lit';

import IaiLitBase from '../../../../IaiLitBase.mjs';
import SearchBox from '../../inputs/SearchBox/search-box.lit.csr.mjs';
import Title from '../../Title/title.lit.csr.mjs';
import Panel from '../../Panel/panel.lit.csr.mjs';
import CrossSearchCard from '../../CrossSearchCard/cross-search-card.lit.csr.mjs';
import Tag from '../../Tag/tag.lit.csr.mjs';
import IaiIcon from '../../../IaiIcon/iai-icon.mjs';
import IaiIconButton from '../../../questionsArchive/IaiIconButton/iai-icon-button.lit.csr.mjs';


export default class QuestionOverviewPage extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        questions: { type: Array },
        consultationName: { type: String },
        _searchValue: { type: String },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-question-overview-page {
                color: var(--iai-silver-color-text);
            }
            iai-question-overview-page ul {
                padding-left: 0;
            }
            iai-question-overview-page li {
                list-style: none;
                margin-top: 1em;
                cursor: pointer;
                transition: background 0.3s ease-in-out;
            }
            iai-question-overview-page li:hover {
                background: var(--iai-silver-color-light);
            }
            iai-question-overview-page iai-silver-cross-search-card .icon-container {
                margin-bottom: 0;
            }
            iai-question-overview-page .response-total {
                display: flex;
                align-items: center;
            }
            iai-question-overview-page .favourite-button {
                margin-top: -0.4em;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();
        this._STORAGE_KEY = "favouriteQuestions";

        // Prop defaults
        this.consultationName = "";
        this.questions = [];

        this._searchValue = "";

        this.applyStaticStyles("iai-question-overview-page", QuestionOverviewPage.styles);
    }

    getStoredIds = () => {
        const storedValue = localStorage.getItem(this._STORAGE_KEY);
        return storedValue ? JSON.parse(storedValue) : [];
    }

    toggleStorage = (newQuestionId) => {
        let questionIds = this.getStoredIds();

        if (questionIds.includes(newQuestionId)) {
            questionIds = questionIds.filter(questionId => questionId != newQuestionId);
        } else {
            questionIds.push(newQuestionId);
        }
        localStorage.setItem(this._STORAGE_KEY, JSON.stringify(questionIds));
    }

    render() {
        return html`
            <section>
                <iai-silver-title
                    .level=${2}
                    .text=${"All consultation questions"}
                    .subtext=${"Browse or search through all questions in this consultation."}
                    .aside=${html`<small>${this.questions.length} questions</small>`}
                    .icon=${"help"}
                ></iai-silver-title>

                <iai-silver-panel>
                    <div slot="content">

                        <iai-silver-search-box
                            .inputId=${"search-value"}
                            .name=${"search-value"}
                            .label=${"Search"}
                            .placeholder=${"Search..."}
                            .value=${this._searchValue}
                            .hideLabel=${true}
                            .handleInput=${(e) => this._searchValue = e.target.value.trim()}
                        ></iai-silver-search-box>

                        <ul>
                            ${this.questions
                                .filter(question => !this._searchValue
                                    || question.title.toLocaleLowerCase().includes(this._searchValue.toLocaleLowerCase()))
                                .map((question, index) => html`
                                <li>
                                    <iai-silver-cross-search-card
                                        @click=${() => window.location.href = question.url}
                                        .type=${"question"}
                                        .title=${`Q${index+1}: ${question.title}`}
                                        .aside=${html`
                                            <iai-icon-button
                                                class="favourite-button"
                                                title="Favourite this question"
                                                @click=${(e) => {
                                                    e.stopPropagation();
                                                    this.toggleStorage(question.id);
                                                }}
                                            >
                                                <iai-icon
                                                    slot="icon"
                                                    name="star"
                                                    .color=${"var(--iai-silver-color-text)"}
                                                    .fill=${0}
                                                ></iai-icon>
                                            </iai-icon-button>
                                        `}
                                        .footer=${html`
                                            <small class="response-total">
                                                ${question.numResponses.toLocaleString()} responses
                                            </small>
                                            <iai-silver-tag
                                                .status=${question.status}
                                                .text=${question.status}
                                                .icon=${"chat_bubble"}
                                            ></iai-silver-tag>
                                        `}
                                        .highlightText=${this._searchValue}
                                    ></iai-silver-cross-search-card>
                                </li>
                            `)}
                        </ul>

                    </div>
                </iai-silver-panel>
            </section>
        `
    }
}
customElements.define("iai-question-overview-page", QuestionOverviewPage);