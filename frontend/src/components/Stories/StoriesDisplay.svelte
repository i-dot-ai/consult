<script lang="ts">
  import clsx from "clsx";

  import { createRawSnippet, onDestroy, onMount } from "svelte";
  import fetchMock from "fetch-mock";

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

  const getSelectedUrlParam = () => {
    return Object.fromEntries(new URLSearchParams(window.location.search))
      .selected;
  };

  const handlePopState = () => {
    selected = getSelectedUrlParam();
  };

  let selected = $state(getSelectedUrlParam());
  let currStory = $state(stories.find((story) => story.name === selected));
  let currStoryTab = $state("interactive");

  $effect(() => {
    // if currStory is declared with derived instead of state
    // prop values do not trigger reactive updates
    // therefore this effect rune is needed
    currStory = stories.find((story) => story.name === selected);
  });

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

  onMount(() => {
    window.addEventListener("popstate", handlePopState);
  });

  onDestroy(() => {
    window.removeEventListener("popstate", handlePopState);
  });

  const categories = [...new Set(stories.map((story) => story.category))];

  $effect.pre(() => {
    const mocks = storyTab?.mocks || currStory?.mocks;
    if (mocks) {
      fetchMock.removeRoutes();

      mocks.forEach((mock) => {
        fetchMock.mockGlobal().route(
          // @ts-expect-error: fetch-mock type not up to date
          { url: mock.url, method: mock.method || "GET" },
          () => {
            if (mock.callback) {
              mock.callback();
            }

            if (mock.throws) {
              throw mock.throws;
            }

            return new Response(mock.body ? JSON.stringify(mock.body) : null, {
              status: mock.status || 200,
            });
          },
        );
      });
    } else {
      fetchMock.unmockGlobal();
    }

    queryClient.resetQueries();
  });
</script>

<div class="grid grid-cols-4 gap-8">
  <aside class="sticky top-4 col-span-1 h-[80vh]">
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
                onclick={(e) => {
                  e.preventDefault();
                  selected = story.name;
                  currStoryTab = "interactive";
                  var newurl = `${window.location.protocol}//${window.location.host}${window.location.pathname}?selected=${story.name}`;
                  window.history.pushState({ path: newurl }, "", newurl);
                }}
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
            {#key currStoryTab}
              <StoryComponent {...storyTab.props as object} />
            {/key}
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
      {:else}
        <p class="my-8 text-center text-neutral-600">
          Please select a component to view
        </p>
      {/if}
    </Panel>
  </div>
</div>

<style>
  :global(div[data-testid="panel-component"]) {
    overflow-y: auto;
  }
</style>
