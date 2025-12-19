<script lang="ts">
  import clsx from "clsx";

  import { slide } from "svelte/transition";

  import { Routes } from "../../../global/routes";
  import { handleEscKeyPress } from "../../../global/utils";

  import IaiIcon from "../../svg/IaiIcon.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import ChevronRight from "../../svg/material/ChevronRight.svelte";
  import Menu from "../../svg/material/Menu.svelte";
  import Button from "../../inputs/Button/Button.svelte";
  import WithExternalClick from "../../WithExternalClick/WithExternalClick.svelte";

  import type { Props } from "./types";

  const {
    title = "Incubator for AI",
    subtitle = "",
    pathParts = [],
    icon = IaiIcon,
    navItems = [{ label: "Home", url: "/" }],
    endItems,
  }: Props = $props();

  let activeSubmenu = $state();
  let mobileExpanded = $state(false);
  let IconComponent = $derived(icon);

  $effect(() => {
    addListeners();
    return () => removeListeners();
  });

  function addListeners() {
    window.addEventListener("keydown", handleEscPress);
  }
  function removeListeners() {
    window.removeEventListener("keydown", handleEscPress);
  }

  function handleEscPress(e: KeyboardEvent) {
    handleEscKeyPress(e, () => (activeSubmenu = null));
  }

  function handleOutsideClick(e: MouseEvent) {
    if (!(e.target as HTMLElement).closest(".nav-button")) {
      activeSubmenu = null;
    }
  }

  function getPathText(i: number, subtitle: string, pathPart: string) {
    return `${i === 0 && !subtitle ? "" : "/"} ${pathPart}`;
  }
</script>

{#snippet navButton(label: string, url?: string)}
  <div class="hover:text-primary">
    <Button variant="ghost" fullWidth={true} size="sm" href={url}>
      <span
        class={clsx([
          "whitespace-nowrap",
          "text-center",
          "md:text-left",
          "py-1",
          "md:py-0",
          "w-full",
        ])}
      >
        {label}
      </span>
    </Button>
  </div>
{/snippet}

{#snippet navigation({ isMobile }: { isMobile: boolean })}
  <nav
    transition:slide
    aria-label="App navigation"
    class={isMobile ? "block md:hidden" : "hidden md:block"}
    data-testid={isMobile ? "mobile-nav" : "desktop-nav"}
  >
    <ol class={clsx([!isMobile && "flex items-center gap-4"])}>
      {#each navItems as navItem, i (i)}
        {@const id = "link-" + navItem.label.toLowerCase().replaceAll(" ", "-")}
        {@const expanded = activeSubmenu === id}

        <li class={isMobile ? "w-full" : "relative"}>
          {#if Array.isArray(navItem.children) && navItem.children.length > 0}
            <WithExternalClick onExternalClick={handleOutsideClick}>
              <button
                class={clsx([
                  "nav-button",
                  "flex",
                  "items-center",
                  "justify-center",
                  "gap-0.5",
                  isMobile &&
                    clsx([
                      "group",
                      "w-full",
                      "hover:bg-neutral-100",
                      "hover:!text-primary",
                    ]),
                ])}
                aria-expanded={expanded ? "true" : "false"}
                aria-controls={id}
                onclick={() => {
                  if (activeSubmenu === id) {
                    activeSubmenu = null;
                  } else {
                    activeSubmenu = id;
                  }
                }}
              >
                {#if isMobile}
                  <div
                    class={clsx([
                      "flex",
                      "items-center",
                      "justify-center",
                      "gap-0.5",
                      "w-full",
                      "-mr-4",
                      "p-2",
                      "text-sm",
                      "text-center",
                      "text-neutral-800",
                      "transition-colors",
                      "whitespace-nowrap",
                      "hover:text-primary",
                    ])}
                  >
                    {navItem.label}

                    <div
                      class={clsx([
                        "transition-transform",
                        expanded && "rotate-90",
                      ])}
                    >
                      <MaterialIcon size="0.9rem" color="fill-neutral-500">
                        <ChevronRight />
                      </MaterialIcon>
                    </div>
                  </div>
                {:else}
                  <span
                    class={clsx([
                      "block",
                      "text-sm",
                      "text-neutral-800",
                      "hover:text-primary",
                      "transition-colors",
                      "whitespace-nowrap",
                    ])}
                  >
                    {navItem.label}
                  </span>

                  <div class="rotate-90">
                    <MaterialIcon size="0.9rem" color="fill-neutral-500">
                      <ChevronRight />
                    </MaterialIcon>
                  </div>
                {/if}
              </button>
            </WithExternalClick>

            {#if activeSubmenu === id || !isMobile}
              <ol
                transition:slide={{ duration: isMobile ? 300 : 0 }}
                {id}
                class={clsx([
                  !isMobile &&
                    clsx([
                      "absolute",
                      "top-6",
                      "right-0",
                      "z-10",
                      "border",
                      "border-neutral-100",
                      "rounded",
                      "bg-white",
                      "shadow-lg",
                      "transition-opacity",
                      !expanded && "pointer-events-none",
                      expanded ? "opacity-1" : "opacity-0",
                    ]),
                ])}
              >
                {#each navItem.children as subItem, i (i)}
                  <li>
                    {@render navButton(subItem.label, subItem.url)}
                  </li>
                {/each}
              </ol>
            {/if}
          {:else}
            {@render navButton(navItem.label, navItem.url)}
          {/if}

          {#if isMobile}
            <hr />
          {/if}
        </li>
      {/each}
    </ol>
  </nav>
{/snippet}

<header class="w-full">
  <div
    class={clsx([
      "flex",
      "justify-between",
      "border-b",
      "border-primary",
      "p-2",
    ])}
  >
    <div class={clsx(["flex", "items-center", "gap-2"])}>
      <a href={Routes.Home} class="block flex items-center gap-2">
        <div
          class={clsx(["flex", "justify-center", "items-center", "w-8", "h-8"])}
        >
          <IconComponent />
        </div>

        <h1 class="font-[500]">
          {title}
        </h1>
      </a>

      <!-- Divider only renders when there's text after -->
      {#if subtitle || pathParts.length > 0}
        <div
          class={clsx([
            "inline-block",
            "min-h-4",
            "mx-2",
            "border-l",
            "border-neutral-300",
            "self-stretch",
          ])}
        ></div>
      {/if}

      <p>
        <span class="text-sm text-neutral-800">
          {subtitle}
        </span>

        <!-- Breadcrumb parts -->
        {#each pathParts as pathPart, i (i)}
          <span
            class={clsx([
              "mr-1",
              "text-xs",
              "text-neutral-500",
              "whitespace-nowrap",
            ])}
          >
            <!--
              Only add slash to first item if subtitle is passed to
              avoid having the vertical divider and slash side by side
            -->
            {getPathText(i, subtitle, pathPart)}
          </span>
        {/each}
      </p>
    </div>

    <div class="ml-4 flex items-center">
      <!-- Mobile menu button -->
      <button
        class={clsx([
          "block",
          "md:hidden",
          "p-1",
          "rounded",
          "border",
          "border-neutral-200",
          "transition-colors",
          "hover:bg-neutral-100",
        ])}
        data-testid="mobile-menu-button"
        onclick={() => (mobileExpanded = !mobileExpanded)}
      >
        <MaterialIcon size="1.5rem" color="fill-neutral-500">
          <Menu />
        </MaterialIcon>
      </button>

      <!-- Desktop nav links -->
      {@render navigation({ isMobile: false })}

      <!-- Extra items to render at the end -->
      {#if endItems}
        <div class="mx-1">
          {@render endItems()}
        </div>
      {/if}
    </div>
  </div>

  {#if mobileExpanded}
    <!-- Mobile nav links -->
    {@render navigation({ isMobile: true })}
  {/if}
</header>
