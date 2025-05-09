import { html, css } from 'lit';
import IaiLitBase from '../../IaiLitBase.mjs';


export default class IaiResponseFilters extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
    }

    static styles = [
        IaiLitBase.styles,
        css``
    ]

    constructor() {
        super();
        this.contentId = this.generateId();
        
        this._SLOT_NAMES = ["filters"]

        this.applyStaticStyles("iai-response-filters", IaiResponseFilters.styles);
    }

    updated() {
        this._SLOT_NAMES.forEach(slotName => this.applySlots(slotName));
    }

    render() {
        return html`
            <div class="iai-filter">
                <div class="iai-filter__header">
                    <div class="iai-filter__header-title">
                        <h2 class="govuk-heading-m">
                            Filter
                        </h2>
                    </div>
                </div>

                <slot name="filters"></slot>
            </div>
        `;
    }
}
customElements.define("iai-response-filters", IaiResponseFilters);