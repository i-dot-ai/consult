<script lang="ts">
  import clsx from "clsx";

  import { createRawSnippet } from "svelte";
  import fetchMock from 'fetch-mock';

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
  import { toTitleCase } from "../../global/utils.ts";
  import { queryClient } from "../../global/queryClient.ts";

  let { selected = "" } = $props();
  let currStory = $state(stories.find((story) => story.name === selected));
  let currStoryTab = $state("interactive");
  let componentProps: unknown = $derived.by(() => {
    let props: unknown = {};
    currStory?.props.forEach((prop) => {
      props[prop.name] = prop.value;
    });
    return props;
  });
  let storyTab = $derived(
    currStory?.stories.find((story) => story.name === currStoryTab),
  );
  let panel: HTMLElement;

  const categories = [...new Set(stories.map((story) => story.category))];

  $effect.pre(() => {
    const mock = storyTab?.mock || currStory?.mock;
    if (mock) {
      fetchMock.removeRoutes();
      fetchMock
        .mockGlobal()
        .route({
          url: mock.url,
          response: mock.response(),
        });
    } else {
      fetchMock.unmockGlobal();
    }

    queryClient.resetQueries();
  })
</script>

<div class="grid grid-cols-4 gap-8">
  <aside class="col-span-1">
    <Panel border={true} bg={false}>
      <ul class="flex flex-col gap-2">
        {#each categories as category (category)}
          <h2 class="font-[500]">{category || "General"}</h2>
          {#each stories.filter((story) => story.category === category) as story (category + story.name)}
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
          <div class="mb-4 flex items-center justify-between">
            <div class="font-[500]">
              <Title level={2} text={currStory.name} />
            </div>

            <Button size="xs" handleClick={() => panel?.requestFullscreen()}>
              <span class="ml-1 mr-1">Fullscreen</span>

              <MaterialIcon color="fill-neutral-500">
                <Fullscreen />
              </MaterialIcon>
            </Button>
          </div>

          <ul>
            {#each [{ name: "interactive" }, ...currStory.stories] as story (story.name)}
              <li>
                <Button
                  variant="ghost"
                  fullWidth={true}
                  handleClick={() => (currStoryTab = story.name)}
                  highlighted={currStoryTab === story.name}
                  highlightVariant="primary"
                >
                  <span class="w-full text-center"
                    >{toTitleCase(story.name)}</span
                  >
                </Button>

                <hr />
              </li>
            {/each}
          </ul>
        </div>

        <div class="mt-4">
          {#if currStoryTab !== "interactive" && storyTab}
            <StoryComponent {...storyTab.props as object} />
          {:else}
            <StoryComponent {...componentProps as object} />

            {#each currStory.props as prop (prop.name)}
              {@const inputId = `input-${prop.name.toLowerCase().replaceAll(" ", "-")}`}

              <div class="mt-4 pl-4">
                {#if ["number", "text", "bool", "select", "json", "html", "func"].includes(prop.type)}
                  <div class="mb-1">
                    <Title level={4} text={prop.name} />
                  </div>
                {/if}

                {#if prop.type === "number"}
                  <input
                    id={inputId}
                    class="rounded-lg border border-neutral-300 p-2"
                    type="number"
                    value={(prop.value as string).toString()}
                    oninput={(e) => {
                      prop.value = parseInt(
                        (e?.target as unknown as { value: string })?.value,
                      );
                    }}
                  />
                {:else if prop.type === "text"}
                  <TextInput
                    id={inputId}
                    label={prop.name}
                    hideLabel={true}
                    value={prop.value! as string}
                    setValue={(newVal) => (prop.value = newVal)}
                  />
                {:else if prop.type === "bool"}
                  <Switch
                    id={inputId}
                    label={prop.name}
                    hideLabel={true}
                    value={prop.value as boolean}
                    handleChange={(newVal) => (prop.value = newVal)}
                  />
                {:else if prop.type === "select"}
                  <Select
                    id={inputId}
                    label={prop.name}
                    hideLabel={true}
                    value={prop.label}
                    items={prop.options! as { value: string; label: string }[]}
                    onchange={(nextVal) => {
                      if (!nextVal) {
                        return;
                      }
                      prop.value = prop.options?.find(
                        (opt: { label: string }) => {
                          return opt.label === nextVal;
                        },
                      )?.value;
                    }}
                  />
                {:else if prop.type === "json"}
                  <CodeMirror
                    value={JSON.stringify(prop.value)}
                    lang={json()}
                    onchange={(newVal) => {
                      prop.value = JSON.parse(newVal);
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

                      prop.value = createRawSnippet(() => ({
                        render: () => newVal,
                      }));
                      prop.rawHtml = newVal;
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
          {/if}
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
