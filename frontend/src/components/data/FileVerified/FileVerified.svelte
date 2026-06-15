<script lang="ts">
  import clsx from "clsx";

  import Panel from "../../dashboard/Panel/Panel.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import CheckCircle from "../../svg/material/CheckCircle.svelte";
  import Title from "../../Title.svelte";

  interface Props {
    numQuestions: number;
  }

  let { numQuestions = 0 }: Props = $props();
</script>

<Panel>
  <div
    class={clsx([
      "flex",
      "flex-col",
      "justify-center",
      "items-center",
      "p-4",
      "pt-8",
    ])}
  >
    <div
      class={clsx([
        "bg-neutral-100",
        "w-24",
        "h-24",
        "rounded-full",
        "flex",
        "items-center",
        "justify-center",
      ])}
    >
      <MaterialIcon color="fill-neutral-600" size="4rem">
        <CheckCircle />
      </MaterialIcon>
    </div>

    <Title level={2}>
      <span class={clsx(["font-bold", "text-lg", "mt-4", "mb-2", "block"])}>
        File structure valid
      </span>
    </Title>
    <p class={clsx(["text-md", "text-center", "text-neutral-600"])}>
      We've successfully validated your data file and there are <br />
      <strong>{numQuestions < 0 ? "0" : numQuestions.toString()}</strong> questions
      detected.
    </p>
  </div>
</Panel>
