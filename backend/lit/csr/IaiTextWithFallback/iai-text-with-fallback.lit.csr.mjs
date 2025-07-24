import { html, css } from 'lit';
import IaiLitBase from '../../IaiLitBase.mjs';


export default class IaiTextWithFallback extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        text: String,
        fallback: String,
        fallbackCondition: Function,
    }
    static styles = [
        IaiLitBase.styles,
        css`
            iai-text-with-fallback .fallback-active {
                font-style: italic;
            }
        `
    ]

    constructor() {
        super();

        this.applyStaticStyles("iai-text-with-fallback", IaiTextWithFallback.styles);
        
        // By default, render fallback if text is falsy
        this.fallbackCondition = (text) => !text;
    }

    render() {
        return html`
            <p class=${this.fallbackCondition(this.text) ? "fallback-active" : ""}>
                ${this.fallbackCondition(this.text) ? this.fallback : this.text}
            </p>
        `
    }
}
customElements.define("iai-text-with-fallback", IaiTextWithFallback)