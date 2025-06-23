import { LitElement, css } from "lit";


export default class IaiLitBase extends LitElement {
    static styles = css`
        :root {
            --iai-colour-focus:  #ffdd04;
            --iai-colour-pink:  #C50878;
            --iai-colour-secondary: #0B8478;
            --iai-colour-secondary-transparent: #0b84781a;
            --iai-colour-pink-transparent: #c5087812;
            --iai-colour-pink-transparent-mid: #F0B5D8;

            --iai-silver-color-light: #f8f9fa;
            --iai-silver-color-mid: rgba(0, 0, 0, 0.3);
            --iai-silver-color-dark: #030213;
            --iai-silver-color-text: rgb(95, 99, 104);
            --iai-silver-color-teal: #0b8478;
            --iai-silver-color-teal-light: #e9f2f1;
        }

        .visually-hidden {
            position: absolute;
            top: 0;
            left: 0;
            width: 0;
            height: 0;
            overflow: hidden;
        }
    `

    static properties = {
        encprops: {type: String},
    }

    constructor() {
        super();
        this.props = {};

        this.CONSULTATION_STATUSES = {
            open: "Open",
            analysing: "Analysing",
            completed: "Completed",
            closed: "Closed",
        }
    }
    
    createRenderRoot() {
        return this;
    }

    willUpdate() {
        if (this.encprops) {
            this.props = JSON.parse(atob(this.encprops)) || {};
        }
    }

    generateId(length=16) {
        const startIndex = 2; //  skip the leading "0."
        return "iai-" + Math.random().toString(36).substring(startIndex, startIndex+length);
    }

    applyStaticStyles(componentTag, cssResult) {
        if (document.querySelector(`style[data-component="${componentTag}"]`)) {
            return;
        }

        const style = document.createElement("style");
        style.setAttribute("data-component", componentTag);

        // cssResult can be an array of cssResult objects, or a single cssResult object
        if (Array.isArray(cssResult)) {
            style.textContent = cssResult.map(result => result.cssText).join("");
        } else {
            style.textContent = cssResult.cssText;
        }
        document.head.append(style);
    }

    applySlots = (slotName) => {
        Promise.resolve().then(() => {
            const slottedChildren = this.querySelectorAll(`:scope > [slot='${slotName}']`);
            const slot = this.querySelector(`slot[name='${slotName}']`);
            slottedChildren.forEach(child => slot.appendChild(child));
        })
    }

    accessibleKeyPressed = (key) => {
        return key === "Enter" || key === " ";
    }
}