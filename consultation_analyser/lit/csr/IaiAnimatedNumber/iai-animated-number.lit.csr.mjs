import { html, css } from 'lit';

import IaiLitBase from '../../IaiLitBase.mjs';


export default class IaiAnimatedNumber extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        number: { type: Number },
        duration: { type: Number }, // miliseconds
        _displayNumber: { type: Number },
    }

    static styles = [
        IaiLitBase.styles,
        css``
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.number = 0;
        this.duration = 1000;
        this._displayNumber = 0;
        
        this.applyStaticStyles("iai-animated-number", IaiAnimatedNumber.styles);
    }

    setDisplayNumber = (newDisplayNumber) => {
        this._displayNumber = newDisplayNumber;
    }

    animate = (start, end, duration) => {
        const setDisplayNumber = (newDisplayNumber) => {
            this._displayNumber = newDisplayNumber;
        }
        const startTime = performance.now();

        function update_number(currTime) {
            const elapsedTime = currTime - startTime;
            const time = Math.min(elapsedTime / duration, 1);
            const currValue = start * (1 - time) + end * time;

            // round to 1 decimal point
            setDisplayNumber(Math.round(currValue * 10) / 10);

            if (time < 1) {
                requestAnimationFrame(update_number);
            }
        }

        requestAnimationFrame(update_number);
    }

    updated(changedProps) {
        if (changedProps.has("number")) {
            this.animate(this._displayNumber, this.number, this.duration);
        }
    }

    render() {
        return html`
            <span>${this._displayNumber}</span>
        `;
    }
}
customElements.define("iai-animated-number", IaiAnimatedNumber);