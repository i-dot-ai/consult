import { html, css } from 'lit';
import IaiLitBase from '../../../IaiLitBase.mjs';


export default class IaiQuestionTiles extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-question-tiles div[slot="tiles"] {
                display: flex;
                flex-wrap: wrap;
                gap: 1em;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        this._SLOT_NAMES = ["tiles"];

        // Prop defaults
        
        this.applyStaticStyles("iai-question-tiles", IaiQuestionTiles.styles);
    }

    updated() {
        this._SLOT_NAMES.forEach(slotName => this.applySlots(slotName));
    }

    render() {
        return html`
            <div class="govuk-grid-row govuk-!-margin-top-5">
                <div class="govuk-grid-column-three-quarters-from-desktop">
                    
                    <slot name="tiles"></slot>

                </div>

                <div class="govuk-grid-column-one-quarter-from-desktop">
                </div>
            </div>
        `;
    }
}
customElements.define("iai-question-tiles", IaiQuestionTiles);