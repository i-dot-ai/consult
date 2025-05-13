import { html, css } from 'lit';
import IaiLitBase from '../../../IaiLitBase.mjs';
import { unsafeHTML } from 'lit/directives/unsafe-html.js';


export default class IaiQuestionBody extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        text: { type: String },
        searchValue: { type: String },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-question-body p {
                line-height: 1.5em;
                font-size: 1.1em;
                margin-block: 0;
                min-height: 6em;
            }
            iai-question-body .matched-text {
                background-color: var(--iai-colour-focus);
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.text = "";
        this.searchValue = "";
        
        this.applyStaticStyles("iai-question-body", IaiQuestionBody.styles);
    }

    getHighlightedText = (fullText, matchedText) => {
        const regex = new RegExp(matchedText, "gi");
        return unsafeHTML(fullText.replace(regex, match => `<span class="matched-text">${match}</span>`));
    }
    
    render() {
        return html`
            <p>${this.getHighlightedText(this.text, this.searchValue)}</p>
        `;
    }
}
customElements.define("iai-question-body", IaiQuestionBody);