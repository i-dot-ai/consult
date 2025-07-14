import { html, css } from 'lit';

import IaiLitBase from '../../../IaiLitBase.mjs';
import IaiAnimatedNumber from '../../IaiAnimatedNumber/iai-animated-number.lit.csr.mjs';
import IaiProgressBar from '../../IaiProgressBar/iai-progress-bar.lit.csr.mjs';
import IaiDataTable from '../../IaiDataTable/iai-data-table.lit.csr.mjs';
import Button from '../Button/button.lit.csr.mjs';
import IaiIcon from '../../IaiIcon/iai-icon.mjs';
import IaiCheckboxInput from '../../inputs/IaiCheckboxInput/iai-checkbox-input.lit.csr.mjs';


export default class ThemesTable extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        themes: { type: Array },
        themeFilters: { type: Array },
        setThemeFilters: { type: Function },
        totalMentions: { type: Number },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-themes-table iai-data-table {
                max-height: 40em;
                overflow: auto;
                display: block;
            }
            iai-themes-table .theme-title {
                font-weight: bold;
                font-size: 0.9em;
                color: var(--iai-silver-color-text);
            }
            iai-themes-table .theme-description {
                white-space: nowrap;
                font-size: 0.9em;
                overflow: hidden;
                max-width: 30em;
                display: block;
                text-overflow: ellipsis;
            }
            iai-themes-table .percentage-cell {
                gap: 0.5em;
                display: flex;
                align-items: center;
            }
            iai-themes-table .title-container {
                display: flex;
                align-items: center;
                gap: 1em;
            }
            iai-themes-table input[type="checkbox"] {
                filter: grayscale(0.5) hue-rotate(75deg);
            }

            iai-themes-table .percentage-cell iai-progress-bar .bar {
                background: var(--iai-silver-color-accent);
            }
            iai-themes-table .percentage-cell iai-progress-bar .container {
                background: var(--iai-silver-color-mid-light);
            }

            iai-themes-table iai-silver-button button {
                width: max-content;
                display: flex;
                align-items: center;
                padding-inline: 0.5em;
                gap: 0.5em;
                font-weight: bold;
                color: var(--iai-silver-color-text);
            }
            iai-themes-table input {
                cursor: pointer;
            }
            iai-themes-table tr {
                transition: background 0.3s ease-in-out;
            }
            iai-themes-table tr:has(input:checked) {
                background: var(--iai-silver-color-teal-light);
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();
        this._NUMBER_ANIMATION_DURATION = 1000;

        this.themes = [];
        this.themeFilters = [];
        this.setThemeFilters = () => {};
        this.totalMentions = 0;

        this.applyStaticStyles("iai-themes-table", ThemesTable.styles);
    }

    render() {
        return html`
            <iai-data-table
                .sortable=${false}
                .data=${this.themes
                    .map(theme => (
                        {
                            // _sortValues are the values used for sorting comparison
                            // instead of the actual value of a cell, which can be an obj etc.
                            // particularly useful for html elements and dates.
                            "_sortValues": {
                                "Mentions": parseInt(theme.mentions),
                                "Percentage": parseInt(theme.percentage),
                                "Theme": theme.title,
                            },
                            "Theme": html`
                                <div class="title-container">
                                    <div>
                                        <input
                                            type="checkbox"
                                            class="theme-checkbox"
                                            id=${"theme-filters" + theme.title.toLowerCase().replace(" ", "-")}
                                            name="theme-filters"
                                            .value=${theme.id}
                                            .checked=${this.themeFilters.includes(theme.id)}
                                            @click=${(e) => {
                                                this.setThemeFilters(e.target.value);
                                            }}
                                        />
                                    </div>
                                    <div>
                                        <span class="theme-title">
                                            ${theme.title}
                                        </span>
                                        <span class="theme-description">
                                            ${theme.description}
                                        </span>
                                    </div>
                                </div>
                            `,
                            "Mentions": html`
                                <iai-animated-number
                                    .number=${theme.mentions}
                                    .duration=${this._NUMBER_ANIMATION_DURATION}
                                ></iai-animated-number>
                            `,
                            "Percentage": html`
                                <div class="percentage-cell">
                                    <div>
                                        <iai-animated-number
                                            .number=${this.getPercentage(theme.mentions, this.totalMentions)}
                                            .duration=${this._NUMBER_ANIMATION_DURATION}
                                        ></iai-animated-number>
                                        %
                                    </div>

                                    <iai-progress-bar
                                        .value=${this.getPercentage(theme.mentions, this.totalMentions)}
                                        .label=${""}
                                    ></iai-progress-bar>
                                </div>
                            `,
                            "Actions": html`
                                <iai-silver-button
                                    .text=${html`
                                        <iai-icon
                                            .name=${"search"}
                                        ></iai-icon>
                                        <span>View responses</span>
                                    `}
                                    .handleClick=${theme.handleClick}
                                ></iai-silver-button>
                            `
                        }
                    ))
                }
            ></iai-data-table>
        `;
    }
}
customElements.define("iai-themes-table", ThemesTable);
