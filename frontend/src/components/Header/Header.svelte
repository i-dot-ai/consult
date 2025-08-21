<script lang="ts">
    import clsx from "clsx";

    import { Routes } from "../../global/routes.ts";

    import type { NavItem } from "../../global/types.ts";

    import GovIcon from "../svg/GovIcon.svelte";
    import MobileMenu from "../MobileMenu.svelte";


    export let isSignedIn: boolean = false;

    function getNavItems(isSignedIn: boolean): NavItem[] {
        return isSignedIn
            ? [
                { text: "Support", url: Routes.Support },
                { text: "Your consultations", url: Routes.Consultations },
                { text: "Sign out", url: Routes.SignOut },
            ]
            : [
                { text: "How it works", url: Routes.HowItWorks },
                { text: "Data sharing", url: Routes.DataSharing },
                { text: "Get involved", url: Routes.GetInvolved },
                { text: "Sign in", url: Routes.SignIn },
            ]
    }
</script>

<header class={clsx([
    "mb-0",
    "bg-black",
    "text-white",
])}>
    <div class={clsx([
        "relative",
        "mx-6"
    ])}>
        <div class={clsx([
            "flex",
            "items-center",
            "justify-between",
            "gap-10",
            "h-12",
        ])}>
            <div class="flex items-center">
                <GovIcon />

                <div class={clsx([
                    "before:block",
                    "before:absolute",
                    "before:top-0",
                    "before:bg-primary",
                    "before:h-full",
                    "before:ml-6",
                    "before:-skew-x-30",
                    "before:w-32",
                ])}>
                    <a href="/" class={clsx([
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
                    ])}>
                        Consult
                    </a>
                </div>
                
                <div class={clsx([
                    "ml-16",
                    "py-0.5",
                    "px-2",
                    "text-md",
                    "font-medium",
                    "uppercase",
                    "bg-gray-500",
                    "hidden",
                    "sm:block",
                ])}>
                    Alpha
                </div>
            </div>

            <nav class="hidden lg:block">
                <ul class="flex gap-4 items-center">
                    {#each getNavItems(isSignedIn) as navItem}
                        <li>
                            <a href={navItem.url} class="hover:underline">
                                {navItem.text}
                            </a>
                        </li>
                    {/each}
                </ul>
            </nav>

            <div class="block lg:hidden">
                <MobileMenu
                    items={getNavItems(isSignedIn)}
                />
            </div>
        </div>
    </div>
</header>