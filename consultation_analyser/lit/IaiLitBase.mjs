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

    willUpdate() {
        if (this.encprops) {
            this.props = JSON.parse(atob(this.encprops)) || {};
        }
    }
}