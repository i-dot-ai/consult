import { html, css } from 'lit';
import IaiLitBase from '../../IaiLitBase.mjs';


export default class IaiResponsesTitle extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        total: {type: Number},
    }

    static styles = [
        IaiLitBase.styles,
        css``
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.total = 0;
        
        this.applyStaticStyles("iai-responses-title", IaiResponsesTitle.styles);
    }

    render() {
        return html`
            <div class="govuk-grid-row">
                <div class="govuk-grid-column-full">
                    <span class="govuk-caption-m">
                        ${this.total} responses
                    </span>
                    <h2 class="govuk-heading-m">
                        Individual responses
                    </h2>
                </div>
            </div>
        `;
    }
}
customElements.define("iai-responses-title", IaiResponsesTitle);