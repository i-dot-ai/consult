import { LitElement, css } from "lit";


export default class IaiLitBase extends LitElement {
    static styles = css``

    static properties = {
        encprops: {type: String},
    }

    constructor() {
        super();
        this.props = {};
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
        return Math.random().toString(36).substring(startIndex, startIndex+length);
    }
}