import { html, css } from 'lit';
import IaiLitBase from '../../../IaiLitBase.mjs';
import IaiQuestionTopbar from '../IaiQuestionTopbar/iai-question-topbar.lit.csr.mjs';
import IaiQuestionBody from '../IaiQuestionBody/iai-question-body.lit.csr.mjs';


export default class IaiQuestionOverview extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        title: { type: String },
        body: { type: String },
        handleClose: { type: Function },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-question-overview .question-overview {
                background: white;
                padding: 1em;
                border-radius: var(--iai-border-radius);
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.title = "";
        this.body = "";
        this.handleClose = () => {};
        
        this.applyStaticStyles("iai-question-overview", IaiQuestionOverview.styles);
    }

    render() {
        return html`
            <div class="question-overview">
                <iai-question-topbar .title=${this.title}>
                    <div slot="buttons">
                        <button title="View question details">O</button>
                        <button
                            title="Close the question overview"
                            @click=${this.handleClose}
                        >X</button>
                    </div>
                </iai-question-topbar>

                <iai-question-body
                    .text=${this.body}
                ></iai-question-body>
            </div>
        `;
    }
}
customElements.define("iai-question-overview", IaiQuestionOverview);