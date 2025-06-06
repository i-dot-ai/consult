import { html, css } from 'lit';
import '@lit-labs/virtualizer';

import IaiLitBase from '../../IaiLitBase.mjs';


export default class IaiVirtualList extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        data: {type: Array},
        renderItem: {type: Function},
        handleScrollEnd: {type: Function},
        message: {type: String},
        _canCallCallback: {type: Boolean},
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-virtual-list {
                display: block;
            }
            iai-virtual-list lit-virtualizer {
                height: 100%;
            }
            iai-virtual-list p.message {
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
        this.data = [];
        this.renderItem = () => console.warn(
            "IaiVirtualList warning: renderResponse prop not passed"
        );
        this.handleScrollEnd = () => {};
        this.message = "";
        this._canCallCallback = true;
        
        this.applyStaticStyles("iai-virtual-list", IaiVirtualList.styles);
    }

    render() {
        if (this.message) {
            return html`<p class="message">${this.message}</p>`;
        }

        return html`
            <lit-virtualizer
                role="list"
                scroller
                .items=${this.data}
                .renderItem=${this.renderItem}
                @scroll=${() => {
                    const lastItem = document.querySelector(".last-item");

                    if (lastItem && this.handleScrollEnd && this._canCallCallback) {
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
customElements.define("iai-virtual-list", IaiVirtualList);