<script>
    import clsx from "clsx";

    import GovIcon from "./svg/GovIcon.svelte";
    import MenuIcon from "./svg/material/MenuIcon.svelte";
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
                ])}>
                    Alpha
                </div>
            </div>
            <hamburger-button role="button" tabindex="0" aria-expanded="false">
                <span>
                    <MenuIcon />
                </span>
            </hamburger-button>
        </div>
    </div>
</header>