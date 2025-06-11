import { html, css } from 'lit';

import IaiLitBase from '../../../IaiLitBase.mjs';
import IaiQuestionTopbar from '../IaiQuestionTopbar/iai-question-topbar.lit.csr.mjs';
import IaiQuestionBody from '../IaiQuestionBody/iai-question-body.lit.csr.mjs';
import IaiIcon from '../../IaiIcon/iai-icon.mjs';
import IaiIconButton from '../IaiIconButton/iai-icon-button.lit.csr.mjs';


export default class IaiQuestionTile extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        _favourited: { type: Boolean },
        questionId: { type: String },
        title: { type: String },
        body: { type: String },
        maxLength: { type: Number },
        highlighted: { type: Boolean },
        searchValue: { type: String },
        handleViewClick: { type: Function },
        handleBodyClick: { type: Function },
        handleFavouriteClick: { type: Function },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-question-tile {
                width: 31%;
            }
            iai-question-tile .question-tile {
                height: 100%;    
                background: white;
                padding: 1em;
                border-radius: var(--iai-border-radius);
                cursor: pointer;
                border: 2px solid transparent;
                transition: 0.3s ease-in-out;
                transition-property: border-color;
            }
            iai-question-tile .question-tile:hover,
            iai-question-tile .question-tile.highlighted {
                border: 2px solid var(--iai-colour-pink);
            }
            iai-question-tile div[slot="buttons"] {
                display: flex;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        this._STORAGE_KEY = "favouriteQuestions";

        // Prop defaults
        this._favourited = false;
        this.questionId = "";
        this.title = "";
        this.body = "";
        this.maxLength = 90;
        this.highlighted = false;
        this.searchValue = "";
        this.handleViewClick = () => {};
        this.handleBodyClick = () => {};
        this.handleFavouriteClick = this.handleFavouriteClick_;

        this.applyStaticStyles("iai-question-tile", IaiQuestionTile.styles);
    }

    getTruncatedText = (text, maxLength) => {
        return text.slice(0, maxLength) + (text.length > maxLength ? "..." : "");
    }

    firstUpdated() {
        this._favourited = this.getStoredIds().includes(this.questionId);
    }

    handleFavouriteClick_ = (e) => {
        e.stopPropagation();

        this.toggleStorage();

        this._favourited = this.getStoredIds().includes(this.questionId);
    }

    getStoredIds = () => {
        const storedValue = localStorage.getItem(this._STORAGE_KEY);
        return storedValue ? JSON.parse(storedValue) : [];
    }

    toggleStorage = () => {
        let questionIds = this.getStoredIds();

        if (questionIds.includes(this.questionId)) {
            questionIds = questionIds.filter(questionId => questionId != this.questionId);
        } else {
            questionIds.push(this.questionId);
        }
        localStorage.setItem(this._STORAGE_KEY, JSON.stringify(questionIds));
    }

    render() {
        return html`
            <div
                class=${"question-tile" + (this.highlighted ? " highlighted" : "")}
                role="button"
                tabindex="0"
                @click=${this.handleBodyClick}
                @keydown=${(e) => {
                    e.stopPropagation();

                    if (e.repeat) {
                        return;
                    }

                    if (this.accessibleKeyPressed(e.key)) {
                        this.handleBodyClick(e);
                    }
                }}
            >
                <iai-question-topbar .title=${this.title}>
                    <div slot="buttons">
                        <iai-icon-button
                            title="View question details"
                            .handleClick=${(e) => {
                                e.stopPropagation();
                                this.handleViewClick(e);
                            }}
                            @keydown=${(e) => e.stopPropagation()}
                        >
                            <iai-icon
                                slot="icon"
                                name="visibility"
                                .color=${"var(--iai-colour-text-secondary)"}
                                .fill=${0}
                            ></iai-icon>
                        </iai-icon-button>

                        <iai-icon-button
                            title="Favourite this question"
                            .handleClick=${(e) => {
                                e.stopPropagation();
                                this.handleFavouriteClick(e);
                            }}
                            @keydown=${(e) => e.stopPropagation()}
                        >    
                            <iai-icon
                                slot="icon"
                                name="star"
                                .fill=${this._favourited ? 1 : 0}
                                .color= ${this._favourited
                                    ? "var(--iai-colour-pink)"
                                    : "var(--iai-colour-text-secondary)"
                                }
                            ></iai-icon>
                        </iai-icon-button>
                    </div>
                </iai-question-topbar>
                
                <iai-question-body
                    .text=${this.getTruncatedText(this.body, this.maxLength)}
                    .searchValue=${this.searchValue}
                ></iai-question-body>
            </div>
        `;
    }
}
customElements.define("iai-question-tile", IaiQuestionTile);