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
            --iai-silver-color-light-darker: #f3f3f5;
            --iai-silver-color-mid-light: #e5e5e5;
            --iai-silver-color-mid: rgba(0, 0, 0, 0.3);
            --iai-silver-color-dark: #030213;
            --iai-silver-color-text: rgb(95, 99, 104);
            --iai-silver-color-teal: #00786f;
            --iai-silver-color-teal-mid: #85d07e;
            --iai-silver-color-teal-light: #f1fdfa;
            --iai-silver-color-accent: #c50978;
            --iai-silver-color-accent-light: #fcf1f6;
            --iai-silver-color-amber: #ba4d00;
            --iai-silver-color-amber-mid: #ffe020;
            --iai-silver-color-amber-light: #fffbea;
            --iai-silver-color-pink: rgb(131, 24, 67);
            --iai-silver-color-pink-mid: rgb(197, 8, 120);
            --iai-silver-color-pink-light: rgb(253, 242, 248);
        }

        .visually-hidden {
            position: absolute;
            top: 0;
            left: 0;
            width: 0;
            height: 0;
            overflow: hidden;
        }

        .matched-text {
            background: yellow;
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
        this._STORAGE_KEYS = {
            FAVOURITE_QUESTIONS: "favouriteQuestions",
        };
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

    getPercentage = (partialValue, totalValue) => {
        if (totalValue === 0) {
            return 0;
        }
        const percentage = (partialValue / totalValue) * 100;

        // Round to 1 decimal point
        return Math.round(percentage * 10) / 10;
    }

    toTitleCase = (text) => {
        return text
            .replace("-", " ")
            .replace(
                /\w\S*/g,
                text => text.charAt(0).toUpperCase() + text.substring(1).toLowerCase()
            );
    }

    getHighlightedText = (fullText, matchedText) => {
        if (!matchedText) {
            return fullText;
        }
        const regex = new RegExp(matchedText, "gi");
        return fullText.replace(regex, match => `<span class="matched-text">${match}</span>`);
    }

    limitChars = (text, maxChars) => {
        return text.length > maxChars
            ? text.substring(0, maxChars) + "..."
            : text
    }

    toggleStorage = (newValue, storageKey) => {
        let existingValues = this.getStoredValues(storageKey);

        if (existingValues.includes(newValue)) {
            existingValues = existingValues.filter(value => value !== newValue);
        } else {
            existingValues.push(newValue);
        }
        localStorage.setItem(storageKey, JSON.stringify(existingValues));
    }

    getStoredValues = (storageKey) => {
        const storedValue = localStorage.getItem(storageKey);
        return storedValue ? JSON.parse(storedValue) : [];
    }
}