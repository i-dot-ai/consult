import { html } from 'lit';
import IaiLitBase from '../../IaiLitBase.mjs';


export default class IaiExpandingText extends IaiLitBase {
    static properties = {
        text: { type: String },
        lines: { type: Number },
        _expanded: { type: Boolean },
    }
    constructor() {
        super();
        this.text = "";
        this.lines = 1;
        this._expanded = false;
    }

    handleClick() {
        this._expanded = !this._expanded;
    }

    render() {
        return html`
            <style>
                iai-expanding-text .iai-text-content {
                    position: relative;
                    width: 100%;
                    padding-left: 1rem;
                }

                iai-expanding-text .iai-text-content:focus-visible {
                    outline: 3px solid #ffdd04;
                    border: 4px solid black;
                }

                iai-expanding-text .iai-text-content::before {
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
                }
            </style>

            <div
                class=${"iai-text-content clickable" + (this._expanded ? "" : " iai-text-truncated")}
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