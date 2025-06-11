import { html, css } from 'lit';

import IaiLitBase from '../../IaiLitBase.mjs';
import IaiIcon from '../IaiIcon/iai-icon.mjs';


export default class IaiExpandingPill extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        label: {type: String},
        body: {type: String},
        initialExpanded: {type: Boolean},
        _expanded: {type: Boolean},
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-expanding-pill {
                font-size: 0.9em;
            }
            
            iai-expanding-pill button {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 0.3em 0.8em;
                gap: 1em;
                font-size: 1em;
                background: #c50878;
                color: white;
                border: none;
                border-radius: var(--iai-border-radius);
                cursor: pointer;
            }
            iai-expanding-pill button.expanded iai-icon {
                transition: transform 0.3s ease-in-out;
                transform: rotate(180deg);
            }
            iai-expanding-pill .body {
                font-size: 1.1em;
                line-height: 1.8em;
                padding: 0 0.5em;
                margin-bottom: 0.5em;
                max-height: 0;
                overflow: hidden;
                transition: 0.6s ease;
                transition-property: max-height, padding;
            }
            iai-expanding-pill .body.expanded {
                padding-block: 0.5em;
                max-height: 10em;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.label = "";
        this.body = "";
        this.initialExpanded = false;
        this._expanded = false;

        this.applyStaticStyles("iai-expanding-pill", IaiExpandingPill.styles);
    }

    firstUpdated() {
        this._expanded = this.initialExpanded;
    }

    render() {
        return html`    
            <button
                class=${this._expanded ? "expanded" : ""}
                @click=${_ => this._expanded = !this._expanded}
            >
                ${this.label}
                <iai-icon
                    .name=${"arrow_drop_down_circle"}
                    .opsz=${12}
                ></iai-icon>
            </button>
            <div class=${"body" + (this._expanded ? " expanded" : "")}>
                ${this.body}
            </div>
        `;
    }
}
customElements.define("iai-expanding-pill", IaiExpandingPill);