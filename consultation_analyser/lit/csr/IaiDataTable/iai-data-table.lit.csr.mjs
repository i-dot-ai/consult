import { html, css } from 'lit';
import IaiLitBase from '../../IaiLitBase.mjs';
import IaiIcon from '../IaiIcon/iai-icon.mjs';


export default class IaiDataTable extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        data: { type: Array },
        initialSorts: { type: Array },
        sortable: { type: Boolean },
        _sortedData: { type: Array },
        _sorts: { type: Array },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-data-table h3 {
                margin: 0;
                font-size: 1em;
            }
            iai-data-table tbody.govuk-table__body td {
                vertical-align: middle;
            }
            iai-data-table .bottom-row td:first-child {
                font-weight: bold;
            }
            iai-data-table .header-button {
                position: relative;
                max-width: max-content;
                margin-right: 1em;
                transition: 0.3s ease-in-out;
                transition-property: color;
                cursor: pointer;
            }
            iai-data-table .header-button:hover {
                color: var(--iai-colour-pink);
            }
            iai-data-table thead {
                text-align: start;
            }
            iai-data-table thead th {
                text-align: left;
                margin-right: 1em;
                padding-right: 2em;
                position: relative;
            }
            iai-data-table .header-button iai-icon {
                position: absolute;
                top: 0;
                right: 0.5em;
                opacity: 0;
                transition: 0.3s ease-in-out;
                transition-property: transform, opacity;
            }
            iai-data-table thead .header-button:hover iai-icon {
                opacity: 0.5;
            }
            iai-data-table thead .header-button.ascending iai-icon,
            iai-data-table thead .header-button.descending iai-icon {
                opacity: 1;
            }
            iai-data-table thead .header-button.ascending iai-icon {
                transform: rotateX(180deg);
            }
            iai-data-table tr.clickable-row {
                cursor: pointer;
                transition: background 0.3s ease-in-out;
            }
            iai-data-table tr.clickable-row:hover {
                background: rgba(0, 0, 0, 0.05);
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // These will not appear as column
        // as they merely act as flags for the row
        this._RESERVED_KEYS = ["_bottomRow", "_sortValues", "_handleClick"];

        // Prop defaults
        this.data = [];
        this.sortable = true;
        this._sorts = [];
        this._sortedData = [];
    }

    firstUpdated() {
        this.applyStaticStyles("iai-data-table", IaiDataTable.styles);

        if (this.initialSorts) {
            this._sorts = this.initialSorts;
        }

        this.updateSortedData();
    }

    updated(changedProps) {
        if (changedProps.has("_sorts") || changedProps.has("data")) {
            this.updateSortedData();
        }
    }

    getHeaders() {
        const keys = new Set();
        const data = this.props.data || this.data;

        data.forEach(row => {
            Object.keys(row)
            .filter(key => !this._RESERVED_KEYS.includes(key))
            .forEach(key => keys.add(key))
        });
        return Array.from(keys);
    }

    updateSorts = (header) => {
        const updatedSorts = [...this._sorts];
        const sortIndex = updatedSorts.findIndex(sort => sort.field === header);

        if (sortIndex === -1) {
            // If sort is not currently applied, apply sort in ascending order
            updatedSorts.unshift({ "field": header, "ascending": true });

        } else {
            // If sort is already applied
            const currentSort = updatedSorts[sortIndex];

            if (sortIndex === 0) {
                // If sort is the last to be applied
                if (currentSort.ascending) {
                    // if ascending make it descending
                    currentSort.ascending = false;
                } else {
                    // if descending order, unapply it
                    updatedSorts.splice(sortIndex, 1);
                }

            } else {
                // If sort is not last to be applied, update it's priority
                updatedSorts.splice(sortIndex, 1);
                updatedSorts.unshift({ "field": header, "ascending": true });
            }
        }

        this._sorts = updatedSorts;
    }

    sort(rows) {
        let result = [...rows];

        result.sort((rowA, rowB) => {
            for (const sort of this._sorts) {
                const direction = sort.ascending ? 1 : -1;

                // If _sortValues specified, use that for sorting instead
                const valA = (rowA._sortValues && rowA._sortValues[sort.field]) || rowA[sort.field];
                const valB = (rowB._sortValues && rowB._sortValues[sort.field]) || rowB[sort.field];

                if (typeof valA === "string") {
                    // Sort strings alphabetically

                    const compResult = valA.localeCompare(valB, undefined, {sensitivity: "base"});
                    if (compResult !== 0) {
                        return compResult * direction;
                    }
                } else if (typeof valA === "number") {
                    // Sort numbers numerically

                    if (valA < valB) {
                        return -1 * direction;
                    }
                    if (valA > valB) {
                        return 1 * direction;
                    }
                } else {
                    // Do not attempt sorting other types
                }
            }
            return 0;
        })
        
        return result;
    }

    updateSortedData() {
        // Rows that have a _bottomRow flag will appear at the bottom
        // and will be sorted as a separate group
        const data = this.props.data || this.data;

        const regularRows = data.filter(row => !row._bottomRow);
        const bottomRows = data.filter(row => row._bottomRow);

        this._sortedData = this.sort(regularRows).concat(this.sort(bottomRows));
    }

    getCurrentSortDirection = (header) => {
        const currentSortIndex = this._sorts.findIndex(sort => sort.field === header);

        if (currentSortIndex === -1) {
            return "";
        }
        return this._sorts[currentSortIndex].ascending ? "ascending" : "descending";
    }

    renderHeader = (header) => {
        if (!this.sortable) {
            return html`
                <th
                    scope="col"
                    class="govuk-table__header"
                >
                    <h3>${header}</h3>
                </th>
            `
        }
        return html`
            <th
                style="" scope="col" class="govuk-table__header"
                class=${"header-button " + this.getCurrentSortDirection(header)}
                role="button"
                aria-sort=${this.getCurrentSortDirection(header)}
                aria-label=${this.getCurrentSortDirection(header)
                    ? `Sorted by "${header}" in ${this.getCurrentSortDirection(header)} order. Click to sort in reverse.`
                    : `Click to sort by "${header}" in ascending order`
                }
                tabindex=0
                @click=${() => this.updateSorts(header)}
                @keydown=${(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        this.updateSorts(header);
                    }
                }}
            >
                <h3>${header}</h3>
                <iai-icon
                    name="sort"
                    .color=${"var(--iai-colour-text-secondary)"}
                    .fill=${0}
                ></iai-icon>
            </th>
        `
    }

    render() {
        const data = this.sortable ? this._sortedData : this.data;

        return html`
            <table class="govuk-table govuk-body" mentionstable="">
                <thead class="govuk-table__head">
                    <tr class="govuk-table__row">    
                        ${this.getHeaders().map(header => this.renderHeader(header))}
                    </tr>
                </thead>
          
                <tbody class="govuk-table__body">
                    ${data.map(row => html`
                        <tr
                            class=${"govuk-table__row"
                                + (row._bottomRow ? " bottom-row" : "")
                                + (row._handleClick ? " clickable-row" : "")
                            }
                            @click=${row._handleClick || undefined}
                        >
                            ${this.getHeaders().map(header => html`
                                <td class="govuk-table__cell">
                                    ${row[header]}
                                </td>
                            `)}
                        </tr>
                    `)}
                </tbody>
            </table>
        `;
    }
}
customElements.define("iai-data-table", IaiDataTable);