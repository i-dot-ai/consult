import { html, css } from 'lit';
import '@lit-labs/virtualizer';

import IaiLitBase from '../../IaiLitBase.mjs';


export default class IaiResponses extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        responses: {type: Array},
        renderResponse: {type: Function},
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-responses {
                display: block;
            }
            iai-responses lit-virtualizer {
                height: 100%;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.responses = [];
        this.renderResponse = () => console.warn(
            "IaiResponses warning: renderResponse prop not passed"
        );
        
        this.applyStaticStyles("iai-responses", IaiResponses.styles);
    }

    render() {
        return html`
            <lit-virtualizer
                role="list"
                scroller
                .items=${this.responses}
                .renderItem=${this.renderResponse}
            ></lit-virtualizer>
        `;
    }
}
customElements.define("iai-responses", IaiResponses);