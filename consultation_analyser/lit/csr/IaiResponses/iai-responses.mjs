import { html, css } from 'lit';
import '@lit-labs/virtualizer';

import IaiLitBase from '../../IaiLitBase.mjs';


export default class IaiResponses extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        responses: {type: Array},
        renderResponse: {type: Function},
        handleScrollEnd: {type: Function},
        message: {type: String},
        _canCallCallback: {type: Boolean},
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
            iai-responses p.message {
                text-align: center;
                font-style: italic;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        this._CALLBACK_COOLDOWN = 2000;

        // Prop defaults
        this.responses = [];
        this.renderResponse = () => console.warn(
            "IaiResponses warning: renderResponse prop not passed"
        );
        this.handleScrollEnd = () => {};
        this.message = "";
        this._canCallCallback = true;
        
        this.applyStaticStyles("iai-responses", IaiResponses.styles);
    }

    render() {
        if (this.message) {
            return html`<p class="message">${this.message}</p>`;
        }

        return html`
            <lit-virtualizer
                role="list"
                scroller
                .items=${this.responses}
                .renderItem=${this.renderResponse}
                @scroll=${() => {
                    const lastResponse = document.querySelector(".last-response");

                    if (lastResponse && this.handleScrollEnd && this._canCallCallback) {
                        this.handleScrollEnd();

                        this._canCallCallback = false;
                        setTimeout(
                            () => this._canCallCallback = true,
                            this._CALLBACK_COOLDOWN
                        );
                    }
                }}
            ></lit-virtualizer>
        `;
    }
}
customElements.define("iai-responses", IaiResponses);