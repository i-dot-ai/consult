import { LitElement, css } from "lit";


export default class IaiLitBase extends LitElement {
    static styles = css``

    static properties = {
        propsString: {type: String},
    }

    constructor() {
        super();
        this.props = {};
    }

    willUpdate() {
        if (this.propsString) {
            this.props = JSON.parse(atob(this.propsString)) || {};
        }
    }
}