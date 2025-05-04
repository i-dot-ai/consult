import { html, css } from 'lit';
import IaiLitBase from '../../../IaiLitBase.mjs';


export default class IaiQuestionTopbar extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        title: { type: String },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-question-topbar {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 0.5em;
                background: white;
                border-radius: var(--iai-border-radius);
            }
            iai-question-topbar .question-title {
                color: var(--iai-colour-pink);
                margin: 0;
                font-size: 1rem;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        this._SLOT_NAMES = ["buttons"];

        // Prop defaults
        this.title = "";
        
        this.applyStaticStyles("iai-question-topbar", IaiQuestionTopbar.styles);
    }
    
    updated() {
        this._SLOT_NAMES.forEach(slotName => this.applySlots(slotName));
    }

    render() {
        return html`
            <h3 class="govuk-heading-m question-title">
                ${this.title}
            </h3>

            <slot name="buttons"></slot>
        `;
    }
}
customElements.define("iai-question-topbar", IaiQuestionTopbar);