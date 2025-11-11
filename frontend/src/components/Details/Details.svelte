<script lang="ts">
  import { type Snippet } from "svelte";

  interface Props {
    summaryText: string;
    children: Snippet;
    open?: boolean;
  }

  let { summaryText, children, open = false }: Props = $props();
</script>

<details class="govuk-details" {open}>
  <summary class="govuk-details__summary">
    <span class="govuk-details__summary-text">
      {summaryText}
    </span>
  </summary>
  <div class="govuk-details__text">
    {@render children()}
  </div>
</details>

<style>
  .govuk-details {
    font-family: "GDS Transport", arial, sans-serif;
    font-weight: 400;
    font-size: 16px;
    line-height: 1.25;
    color: #0b0c0c;
    margin-bottom: 20px;
  }

  .govuk-details__summary {
    display: inline-block;
    position: relative;
    padding-left: 25px;
    color: #1d70b8;
    cursor: pointer;
  }

  .govuk-details__summary:hover {
    color: #003078;
  }

  .govuk-details__summary:focus {
    outline: 3px solid #fd0;
    outline-offset: 0;
    background-color: #fd0;
  }

  .govuk-details__summary:before {
    content: "";
    position: absolute;
    top: -1px;
    left: 0;
    width: 0;
    height: 0;
    border-style: solid;
    border-color: transparent;
    -webkit-clip-path: polygon(0% 0%, 0% 100%, 100% 50%);
    clip-path: polygon(0% 0%, 0% 100%, 100% 50%);
    border-width: 7px 0 7px 12.124px;
    border-left-color: inherit;
  }

  .govuk-details[open] > .govuk-details__summary:before {
    -webkit-clip-path: polygon(0% 0%, 50% 100%, 100% 0%);
    clip-path: polygon(0% 0%, 50% 100%, 100% 0%);
    border-width: 12.124px 7px 0 7px;
    border-top-color: inherit;
    border-left-color: transparent;
  }

  .govuk-details__summary-text {
    text-decoration: underline;
    text-decoration-thickness: max(1px, 0.0625rem);
    text-underline-offset: 0.1578em;
  }

  .govuk-details__text {
    padding: 15px 0 0 25px;
    border-left: 5px solid #b1b4b6;
    padding-left: 20px;
    margin-left: 25px;
  }

  @media (min-width: 40.0625em) {
    .govuk-details {
      font-size: 19px;
      line-height: 1.31579;
    }
  }
</style>