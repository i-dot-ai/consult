<script lang="ts">
  import clsx from "clsx";

  import { Routes } from "../../global/routes.ts";

  import type { NavItem } from "../../global/types.ts";

  import GovIcon from "../svg/GovIcon.svelte";
  import MobileMenu from "../MobileMenu.svelte";

  export let isStaff: boolean = false;
  export let email: string | null = null;

  function getNavItems(email: string | null, isStaff: boolean): NavItem[] {
    if (!email ) {
      return [
        { text: "How it works", url: Routes.HowItWorks },
        { text: "Data sharing", url: Routes.DataSharing },
        { text: "Get involved", url: Routes.GetInvolved },
      ];
    } else {
      if (isStaff) {
        return [
          { text: "Consultations", url: Routes.SupportConsultations },
          { text: "Users", url: Routes.SupportUsers },
          { text: "Import", url: Routes.SupportImport },
          { text: "Sign-off", url: Routes.SupportSignOff },
          { text: "Themefinder", url: Routes.SupportThemefinder },
          { text: `Sign out ${email}`, url: Routes.SignOut },
        ];
      } else {
        return [
          { text: "Support", url: Routes.Support },
          { text: "Your consultations", url: Routes.Consultations },
          { text: `Sign out ${email}`, url: Routes.SignOut },
        ];
      }
    }
  }
</script>

<header class={clsx(["mb-0", "bg-black", "text-white", "px-4", "md:px-24"])}>
  <div class={clsx(["relative", "mx-6"])}>
    <div
      class={clsx([
        "flex",
        "items-center",
        "justify-between",
        "gap-10",
        "h-12",
      ])}
    >
      <div class="flex items-center">
        <GovIcon />

        <div
          class={clsx([
            "before:block",
            "before:absolute",
            "before:top-0",
            "before:bg-primary",
            "before:h-full",
            "before:ml-6",
            "before:-skew-x-[30deg]",
            "before:w-32",
          ])}
        >
          <a
            href={!email ? Routes.Home: Routes.Consultations}
            class={clsx([
              "flex",
              "justify-center",
              "items-center",
              "relative",
              "left-4",
              "h-full",
              "w-full",
              "px-0",
              "pr-2",
              "pl-8",
              "text-white",
              "text-2xl",
              "no-underline",
            ])}
          >
            Consult
          </a>
        </div>

        <div
          class={clsx([
            "ml-16",
            "py-0.5",
            "px-2",
            "text-md",
            "font-medium",
            "uppercase",
            "bg-gray-500",
            "hidden",
            "sm:block",
          ])}
        >
          Alpha
        </div>
      </div>

      <nav class="hidden lg:block">
        <ul class="flex items-center gap-4">
          {#each getNavItems(isSignedIn, isStaff) as navItem (navItem.text)}
            <li>
              <a href={navItem.url} class="hover:underline">
                {navItem.text}
              </a>
            </li>
          {/each}
        </ul>
      </nav>

      <div class="block lg:hidden">
        <MobileMenu items={getNavItems(email, isStaff)} />
      </div>
    </div>
  </div>
</header>