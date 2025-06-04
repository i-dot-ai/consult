import { html, css } from 'lit';

import IaiLitBase from '../../IaiLitBase.mjs';
import IaiIcon from '../questionsArchive/IaiIcon/iai-icon.mjs';
import IaiIconButton from '../questionsArchive/IaiIconButton/iai-icon-button.lit.csr.mjs';


export default class IaiChip extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        label: {type: String},
        handleClick: {type: Function},
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-chip {
                font-size: 0.9em;
            }
            
            iai-chip div {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 1em;
                padding: 0.5em 1em;
                font-size: 1em;
                line-height: 1.5em;
                color: black;
                background: var(--iai-colour-pink-transparent-mid);
                border: none;
                border-radius: var(--iai-border-radius);
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.label = "";
        this.handleClick = () => {};

        this.applyStaticStyles("iai-chip", IaiChip.styles);
    }

    render() {
        return html`    
            <div>
                <span>
                    ${this.label}
                </span>

                <iai-icon-button
                    title="Remove theme filter"
                    .handleClick=${this.handleClick}
                >
                    <iai-icon
                        slot="icon"
                        name="close"
                        .opsz=${12}
                        .color=${"black"}
                    ></iai-icon>
                </iai-icon-button>
            </div>
        `;
    }
}
customElements.define("iai-chip", IaiChip);