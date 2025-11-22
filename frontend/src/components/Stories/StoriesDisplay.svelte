<script lang="ts">
  import clsx from "clsx";

  import { createRawSnippet, type Component } from "svelte";

  import CodeMirror from "svelte-codemirror-editor";
  import { json } from "@codemirror/lang-json";

  import Panel from "../dashboard/Panel/Panel.svelte";
  import Title from "../Title.svelte";
  import TextInput from "../inputs/TextInput/TextInput.svelte";
  import Switch from "../inputs/Switch/Switch.svelte";
  import Button from "../inputs/Button/Button.svelte";
  import Select from "../inputs/Select/Select.svelte";
  import Tag from "../Tag/Tag.svelte";
  import MaterialIcon from "../MaterialIcon.svelte";
  import Fullscreen from "../svg/material/Fullscreen.svelte";

  import stories from "./stories.ts";

  let { selected = "" } = $props();
  let currStory: Story | undefined = $state(
    stories.find((story) => story.name === selected),
  );
  let componentProps: Object = $derived.by(() => {
    let props = {};
    currStory?.props.forEach((prop) => {
      props[prop.name] = prop.value;
    });
    return props;
  });
  let panel;

  const categories = [...new Set(stories.map((story) => story.category))];
</script>

<div class="grid grid-cols-4 gap-8">
  <aside class="col-span-1">
    <Panel border={true} bg={false}>
      <ul class="flex flex-col gap-2">
        {#each categories as category}
          <h2 class="font-[500]">{category || "General"}</h2>
          {#each stories.filter((story) => story.category === category) as story}
            <li>
              <a
                href={`/stories?selected=${story.name}`}
                class={clsx([
                  "block",
                  "w-full",
                  "h-full",
                  "px-2",
                  "py-1",
                  "rounded-lg",
                  "transition-colors",
                  "text-neutral-700",
                  "hover:text-pink-500",
                  "hover:bg-neutral-100",
                  currStory?.name === story.name &&
                    "text-primary hover:text-pink-600",
                ])}
              >
                {story.name}
              </a>
            </li>
          {/each}
        {/each}
      </ul>
    </Panel>
  </aside>

  <div class="col-span-3 bg-white" bind:this={panel}>
    <Panel>
      {#if currStory}
        {@const StoryComponent = currStory.component}

        <div>
          <div class="mb-4 flex justify-between items-center">
            <div class="font-[500]">
              <Title level={2} text={currStory.name} />
            </div>

            <Button size="xs" handleClick={() => panel?.requestFullscreen()}>
              <span class="mr-1 ml-1">Fullscreen</span>

              <MaterialIcon color="fill-neutral-500">
                <Fullscreen />
              </MaterialIcon>
            </Button>
          </div>

          {#each currStory.stories as story}
            <div class="mb-4 last:mb-0">
              <h3>{story.name}</h3>
              <StoryComponent {...story.props} />
            </div>
          {/each}
        </div>

        <hr class="my-8" />

        <div>
          <h3>Interactive</h3>

          <StoryComponent {...componentProps} />

          {#each currStory.props as prop}
            {@const inputId = `input-${prop.name.toLowerCase().replaceAll(" ", "-")}`}

            <div class="pl-4 mt-4">
              {#if ["number", "text", "bool", "select", "json", "html", "func"].includes(prop.type)}
                <div class="mb-1">
                  <Title level={4} text={prop.name} />
                </div>
              {/if}

              {#if prop.type === "number"}
                <input
                  id={inputId}
                  class="border border-neutral-300 rounded-lg p-2"
                  type="number"
                  value={prop.value.toString()}
                  oninput={(e: any) => {
                    prop.value = parseInt(e.target.value);
                  }}
                />
              {:else if prop.type === "text"}
                <TextInput
                  id={inputId}
                  label={prop.name}
                  hideLabel={true}
                  value={prop.value}
                  setValue={(newVal) => (prop.value = newVal)}
                />
              {:else if prop.type === "bool"}
                <Switch
                  id={inputId}
                  label={prop.name}
                  hideLabel={true}
                  value={prop.value}
                  handleChange={(newVal) => (prop.value = newVal)}
                />
              {:else if prop.type === "select"}
                <Select
                  id={inputId}
                  label={prop.name}
                  hideLabel={true}
                  value={prop.label}
                  items={prop.options.map((opt: any) => ({
                    value: opt.label,
                    label: opt.label,
                  }))}
                  onchange={(nextVal) => {
                    if (!nextVal) {
                      return;
                    }
                    prop.value = prop.options.find((opt: any) => {
                      return opt.label === nextVal;
                    }).value;
                  }}
                />
              {:else if prop.type === "json"}
                <CodeMirror
                  value={JSON.stringify(prop.value)}
                  lang={json()}
                  onchange={(newVal) => {
                    try {
                      prop.value = JSON.parse(newVal);
                    } catch {}
                  }}
                />
              {:else if prop.type === "html"}
                <CodeMirror
                  value={prop.rawHtml}
                  lang={json()}
                  onchange={(newVal) => {
                    // return if not valid html
                    const doc = document.createElement("div");
                    doc.innerHTML = newVal;
                    if (!newVal || doc.innerHTML !== newVal) {
                      return;
                    }

                    try {
                      prop.value = createRawSnippet(() => ({
                        render: () => newVal,
                      }));
                      prop.rawHtml = newVal;
                    } catch {}
                  }}
                />
              {:else if prop.type === "func"}
                <Tag>
                  <span class="italic">
                    Function: {prop.schema || "No schema provided"}
                  </span>
                </Tag>
              {/if}
            </div>
          {/each}
        </div>
      {/if}
    </Panel>
  </div>
</div>

<style>
  :global(div[data-testid="panel-component"]) {
    overflow-y: auto;
  }
</style>
