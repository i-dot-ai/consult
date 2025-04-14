import { html } from 'lit';
import IaiLitBase from '../../IaiLitBase.mjs';


export default class IaiExpandingText extends IaiLitBase {
    static properties = {
        text: { type: String },
        lines: { type: Number },
        _expanded: { type: Boolean },
        _textOverflowing: { type: Boolean },
    }
    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.text = "";
        this.lines = 1;
        this._expanded = false;
        this._textOverflowing = true;
    }

    handleClick() {
        if (!this._textOverflowing) {
            return;
        }
        this._expanded = !this._expanded;
    }

    isTextOverflowing = (element, lines) => {
        let computedLineHeight = parseInt(window.getComputedStyle(element).lineHeight);
        const scrollHeight = this.querySelector(".iai-text-content").scrollHeight;
        return Math.round(scrollHeight / computedLineHeight) > lines;
    }

    updateTextOverflowing = () => {
        this._textOverflowing = this.isTextOverflowing(
            this.querySelector(".iai-text-content"),
            this.lines
        );
    } 

    firstUpdated() {
        this.updateTextOverflowing();

        window.addEventListener("resize", this.updateTextOverflowing);
    }

    disconnectedCallback() {
        window.removeEventListener("resize", this.updateTextOverflowing);

        super.disconnectedCallback();
    }

    render() {
        return html`
            <style>
                .iai-text-content:has(#${this.contentId}) {
                    transition-property: color, padding-left;
                    transition: 0.3s ease-in-out;
                    padding-left: 0em;
                    position: relative;
                    width: 100%;
                    line-height: 1.3em;
                }
                .iai-text-content:has(#${this.contentId}).clickable {
                    padding-left: 1em;
                }
                .iai-text-content:has(#${this.contentId}).clickable:focus-visible {
                    outline: 3px solid var(--iai-colour-focus);
                    border: 4px solid black;
                }
                .iai-text-content:has(#${this.contentId}).clickable::before {
                    content: "${this._expanded ? "▾" : "▸"}";
                    position: absolute;
                    left: 0;
                    top: 0;
                }
                .iai-text-content:has(#${this.contentId}).iai-text-truncated {
                    display: -webkit-box;
                    -webkit-line-clamp: ${this.lines};
                    -webkit-box-orient: vertical;
                    overflow: hidden;
                    text-overflow: ellipsis;

                    display: box;
                    line-clamp: ${this.lines};
                    box-orient: vertical;
                }
            </style>

            <div
                class=${"iai-text-content"
                    + (this._textOverflowing ? " clickable" : "")
                    + (this._expanded ? "" : " iai-text-truncated")
                }
                role="button"
                aria-expanded=${this._expanded}
                aria-controls=${this.contentId}
                tabindex="0"
                @keydown=${(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        this.handleClick();
                    }
                }}
                @click=${this.handleClick}
            >
                <span id=${this.contentId}>
                    ${this.text}
                </span>
            </div>
        `;
    }
}
customElements.define("iai-expanding-text", IaiExpandingText);