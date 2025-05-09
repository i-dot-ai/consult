import { html, css } from 'lit';

import IaiLitBase from '../../IaiLitBase.mjs';


export default class IaiPageTitle extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        title: { type: String },
        subtitle: { type: String },
    }

    static styles = [
        IaiLitBase.styles,
        css``
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.title = "";
        this.subtitle = "";
        
        this.applyStaticStyles("iai-page-title", IaiPageTitle.styles);
    }

    render() {
        return html`
            <div class="govuk-grid-row govuk-!-margin-top-5">
                <div class="govuk-grid-column-three-quarters-from-desktop tile-panel">
                    <h2 class="govuk-heading-s">${this.subtitle}</h2>
                    <h1 class="govuk-heading-l">${this.title}</h1>
                </div>
            </div>
        `;
    }
}
customElements.define("iai-page-title", IaiPageTitle);