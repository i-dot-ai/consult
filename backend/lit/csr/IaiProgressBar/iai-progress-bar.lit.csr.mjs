import { html, css } from 'lit';

import IaiLitBase from '../../IaiLitBase.mjs';


export default class IaiProgressBar extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        value: { type: Number },
        label: { type: String },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-progress-bar .container {
                border: 1px dotted;
            }
            iai-progress-bar .container .bar {
                display: flex;
                justify-content: end;
                align-items: center;
                position: relative;
                height: 2em;
                color: white;
                transition: width 1s ease-in-out;
                background: var(--iai-colour-pink);
            }
            iai-progress-bar .container .label {
                display: block;    
                position: absolute;
                right: 0.5em;
                text-align: right;
                color: white;
                font-weight: bold;
            }
            iai-progress-bar .container.low-value .label {
                left: calc(100% + 0.5em);
                color: var(--iai-colour-pink);
                font-size: 1.2em;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.value = 0;
        this.label = "";
        
        this.applyStaticStyles("iai-progress-bar", IaiProgressBar.styles);
    }

    getWidth() {
        if (this.value > 100) {
            return 100;
        }
        if (this.value < 0) {
            return 0;
        }
        return this.value;
    }

    render() {
        return html`
            <div class=${"container" + (this.value < 30 ? " low-value" : "")}>
                <div class=${"bar" + (this.value >= 100 ? " full" : "")} style=${`width: ${this.getWidth()}%;`}>
                    ${this.label
                        ? html`
                            <span class="label">
                                ${this.label}
                            </span>
                        `
                        : ""
                    }
                </div>
            </div>
        `;
    }
}
customElements.define("iai-progress-bar", IaiProgressBar);