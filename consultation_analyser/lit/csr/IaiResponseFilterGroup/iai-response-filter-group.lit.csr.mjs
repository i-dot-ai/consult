import { html, css } from 'lit';
import IaiLitBase from '../../IaiLitBase.mjs';


export default class IaiResponseFilterGroup extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        title: { type: String },
    }

    static styles = [
        IaiLitBase.styles,
        css``
    ]

    constructor() {
        super();
        this.contentId = this.generateId();
        
        this._SLOT_NAMES = ["content"]
        
        // Prop defaults
        this.title = "";
        
        this.applyStaticStyles("iai-response-filter-group", IaiResponseFilterGroup.styles);
    }

    updated() {
        this._SLOT_NAMES.forEach(slotName => this.applySlots(slotName));
    }

    render() {
        return html`
            <div class="govuk-form-group">
                <fieldset class="govuk-fieldset">
                    <legend class="govuk-fieldset__legend govuk-fieldset__legend--m">
                        ${this.title}
                    </legend>

                    <slot name="content"></slot>

                </fieldset>
            </div>      
        `;
    }
}
customElements.define("iai-response-filter-group", IaiResponseFilterGroup);