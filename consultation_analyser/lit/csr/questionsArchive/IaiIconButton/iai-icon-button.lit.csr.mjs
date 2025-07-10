import { html, css } from 'lit';

import IaiLitBase from '../../../IaiLitBase.mjs';


export default class IaiIconButton extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        title: { type: String },
        handleClick: { type: Function },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-icon-button button {
                background: none;
                border: none;
                cursor: pointer;
                border-radius: 0.5em;
                padding: 0.3em 0.5em;
                transition: 0.3s ease-in-out;
                transition-property: background-color, color;
            }
            iai-icon-button button:hover {
                color: black;
                background: #cbfbf1;
            }
            iai-icon-button iai-icon {
                font-size: 1.2em;
            }
            iai-icon-button iai-icon iai-icon {
                position: absolute;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        this._SLOT_NAMES = ["icon"];

        // Prop defaults
        this.title = "";
        this.handleClick = () => {};
        
        this.applyStaticStyles("iai-icon-button", IaiIconButton.styles);
    }

    updated() {
        this._SLOT_NAMES.forEach(slotName => this.applySlots(slotName));
    }

    render() {
        return html`
            <button
                type="button"
                title=${this.title}
                @click=${this.handleClick}
            >
                <slot name="icon"></slot>
            </button>
        `;
    }
}
customElements.define("iai-icon-button", IaiIconButton);