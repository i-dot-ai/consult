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
    position: relative;
    color: var(--color-primary);
    cursor: pointer;
  }

  .govuk-details__summary:hover {
    text-decoration: underline;
  }

  .govuk-details__summary-text {
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