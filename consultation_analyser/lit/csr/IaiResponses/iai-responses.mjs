import { html, css } from 'lit';
import '@lit-labs/virtualizer';

import IaiLitBase from '../../IaiLitBase.mjs';


export default class IaiResponses extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        responses: {type: Array},
        renderResponse: {type: Function},
        handleScrollEnd: {type: Function},
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
            iai-responses p.not-found {
                text-align: center;
                font-style: italic;
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
        this.handleScrollEnd = () => {}
        
        this.applyStaticStyles("iai-responses", IaiResponses.styles);
    }

    render() {
        if (this.responses.length === 0) {
            return html`<p class="not-found">No matching responses found</p>`
        }

        return html`
            <lit-virtualizer
                role="list"
                scroller
                .items=${this.responses}
                .renderItem=${this.renderResponse}
                @scroll=${() => {
                    const lastResponse = document.querySelector(".last-response");
                    
                    if (lastResponse && this.handleScrollEnd) {
                        this.handleScrollEnd();
                    }
                }}
            ></lit-virtualizer>
        `;
    }
}
customElements.define("iai-responses", IaiResponses);