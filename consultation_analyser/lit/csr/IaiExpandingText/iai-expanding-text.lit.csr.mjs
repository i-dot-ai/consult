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
        const lineHeight = parseInt(window.getComputedStyle(element).lineHeight.replace("px", ""));
        const scrollHeight = this.querySelector(".iai-text-content").scrollHeight;
        return scrollHeight / lineHeight > this.lines;
    }

    updateTextOverflowing = () => {
        this._textOverflowing = this.isTextOverflowing(
            this.querySelector(".iai-text-content"),
            this.lines
        )
    } 

    firstUpdated() {
        this.updateTextOverflowing();

        window.addEventListener("resize", () => {
            this.updateTextOverflowing();
        })        
    }

    render() {
        return html`
            <style>
                iai-expanding-text .iai-text-content {
                    transition-property: color, padding-left;
                    transition: 0.3s ease-in-out;
                    padding-left: 0rem;
                    position: relative;
                    width: 100%;
                }
                iai-expanding-text .iai-text-content.clickable {
                    padding-left: 1rem;
                }
                iai-expanding-text .iai-text-content.clickable:focus-visible {
                    outline: 3px solid var(--iai-colour-focus);
                    border: 4px solid black;
                }
                iai-expanding-text .iai-text-content.clickable::before {
                    content: "${this._expanded ? "▾" : "▸"}";
                    position: absolute;
                    left: 0;
                    top: 0;
                }
                iai-expanding-text .iai-text-content.iai-text-truncated {
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
                tabindex="0"
                @keydown=${(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        this.handleClick();
                    }
                }}
                @click=${this.handleClick}
            >
                ${this.text}
            </div>
        `;
    }
}
customElements.define("iai-expanding-text", IaiExpandingText);