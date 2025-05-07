import { html, css } from 'lit';

import IaiLitBase from '../../../IaiLitBase.mjs';


export default class IaiQuestionOverviewSubtitle extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        title: { type: String },
        total: { type: Number },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-question-overview-subtitle {
                display:flex;
                justify-content: space-between;
                align-items: center;
            }
            iai-question-overview-subtitle .total {
                font-size: 1.1em;
            }
            iai-question-overview-subtitle h3 {
                font-size: 0.9em;
                color: var(--iai-colour-secondary);
                margin: 0;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.title = "";
        this.total = 0;
        
        this.applyStaticStyles("iai-question-overview-subtitle", IaiQuestionOverviewSubtitle.styles);
    }

    render() {
        return html`
            <h3>
                ${this.title}
            </h3>
            <div class="total">
                Total: <strong>${this.total}</strong>
            </div>
        `;
    }
}
customElements.define("iai-question-overview-subtitle", IaiQuestionOverviewSubtitle);