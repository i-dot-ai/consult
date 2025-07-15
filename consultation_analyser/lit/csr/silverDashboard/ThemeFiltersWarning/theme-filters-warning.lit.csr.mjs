import { html, css } from 'lit';

import IaiLitBase from '../../../IaiLitBase.mjs';

import Button from '../Button/button.lit.csr.mjs';
import IaiIcon from '../../IaiIcon/iai-icon.mjs';
import IaiIconButton from '../../questionsArchive/IaiIconButton/iai-icon-button.lit.csr.mjs';
import Tag from '../Tag/tag.lit.csr.mjs';


export default class ThemeFiltersWarning extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        themes: { type: Array },
        themeFilters: { type: Array },
        updateThemeFilters: { type: Function },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-theme-filters-warning .theme-tag .material-symbols-outlined {
                font-size: 1.3em;
            }
            iai-theme-filters-warning iai-silver-button button {
                width: max-content;
                display: flex;
                align-items: center;
                padding-inline: 0.5em;
                gap: 0.5em;
                font-weight: bold;
                color: var(--iai-silver-color-text);
            }
            iai-theme-filters-warning iai-silver-tag {
                width: 100%;
                display: block;
                margin-bottom: 1em;
            }
            iai-theme-filters-warning .tag-container iai-silver-tag {
                width: auto;
                margin: 0;
            }
            iai-theme-filters-warning iai-silver-tag .tag-container {
                display: flex;
                gap: 0.5em;
                align-items: center;
                flex-wrap: wrap;
            }
            iai-theme-filters-warning iai-silver-tag .theme-tag {
                display: flex;
                gap: 0.5em;
                font-size: 1.2em;
                align-items: center;
            }
            iai-theme-filters-warning iai-silver-tag .theme-tag iai-icon-button {
                margin-top: 0.1em;
            }
            iai-theme-filters-warning iai-silver-tag .tag {
                width: 100%;
            }
            iai-theme-filters-warning iai-silver-button button {
                width: max-content;
                display: flex;
                align-items: center;
                padding-inline: 0.5em;
                gap: 0.5em;
                font-weight: bold;
                color: var(--iai-silver-color-text);
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        this.themes = [];
        this.themeFilters = [];
        this.updateThemeFilters = () => {};

        this.applyStaticStyles("iai-theme-filters-warning", ThemeFiltersWarning.styles);
    }
    
    render() {
        return html`
            <iai-silver-tag
                .status=${"Analysing"}
                .icon=${"report"}
                .text=${`Selected themes (${this.themeFilters.length})`}
                .subtext=${html`
                    <div class="tag-container">
                        ${this.themeFilters.map(themeFilter => html`
                        <iai-silver-tag
                            .text=${html`
                                <div class="theme-tag">
                                    ${this.themes.find(theme => theme.id == themeFilter).title}

                                    <iai-icon-button .handleClick=${() => this.updateThemeFilters(themeFilter)}>
                                        <iai-icon
                                            slot="icon"
                                            .name=${"close"}
                                        ></iai-icon>
                                    </iai-icon-button>
                                    
                                </div>`}
                        ></iai-silver-tag>
                        `)}

                        <iai-silver-button
                            .text=${"Clear all"}
                            .handleClick=${() => this.updateThemeFilters()}
                        ></iai-silver-button>
                    </div>
                `}
            >
            </iai-silver-tag>
        `;
    }
}
customElements.define("iai-theme-filters-warning", ThemeFiltersWarning);
