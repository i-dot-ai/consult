import { html, css } from 'lit';

import IaiLitBase from '../../../IaiLitBase.mjs';
import IaiQuestionTopbar from '../IaiQuestionTopbar/iai-question-topbar.lit.csr.mjs';
import IaiQuestionBody from '../IaiQuestionBody/iai-question-body.lit.csr.mjs';


export default class IaiQuestionTile extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        body: { type: String },
        title: { type: String },
        maxLength: { type: Number },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-question-tile {
                width: 30%;
            }
            iai-question-tile .question-tile {
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
        this.maxLength = 90;
        
        this.applyStaticStyles("iai-question-tile", IaiQuestionTile.styles);
    }

    getTruncatedText = (text, maxLength) => {
        return text.slice(0, maxLength) + (text.length > maxLength ? "..." : "");
    }

    render() {
        return html`
            <div class="question-tile">
                <iai-question-topbar .title=${this.title}>
                    <div slot="buttons">
                        <button title="View question details">O</button>
                        <button title="Favourite this question">X</button>
                    </div>
                </iai-question-topbar>
                
                <iai-question-body
                    .text=${this.getTruncatedText(this.body, this.maxLength)}
                ></iai-question-body>
            </div>
        `;
    }
}
customElements.define("iai-question-tile", IaiQuestionTile);