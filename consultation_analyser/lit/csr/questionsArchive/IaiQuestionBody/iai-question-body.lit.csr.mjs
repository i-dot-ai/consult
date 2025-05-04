import { html, css } from 'lit';
import IaiLitBase from '../../../IaiLitBase.mjs';


export default class IaiQuestionBody extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        text: { type: String },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-question-body p {
                line-height: 1.5em;
                font-size: 1.1em;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.text = "";
        
        this.applyStaticStyles("iai-question-body", IaiQuestionBody.styles);
    }
    
    render() {
        return html`
            <p>${this.text}</p>
        `;
    }
}
customElements.define("iai-question-body", IaiQuestionBody);