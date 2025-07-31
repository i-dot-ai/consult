<script lang="ts">
    import clsx from "clsx";

    export let title: string;
    export let mentions: number;
    export let uniqueRespondents: number;
    export let questions: string[];

    function formatNumber(num: number): string {
        return num.toLocaleString();
    }
</script>

<div class={clsx([
    "bg-white",
    "border",
    "border-gray-200",
    "rounded-lg",
    "p-6",
    "hover:shadow-md",
    "transition-shadow",
    "duration-200",
])}>
    <!-- Theme Title -->
    <h3 class={clsx([
        "text-lg",
        "font-semibold",
        "text-gray-900",
        "mb-4",
        "leading-tight",
    ])}>
        {title}
    </h3>

    <!-- Main Metrics -->
    <div class={clsx([
        "flex",
        "items-center",
        "justify-between",
        "mb-2",
    ])}>
        <span class={clsx([
            "text-xl",
            "font-bold",
            "text-gray-900",
        ])}>
            {formatNumber(mentions)} mentions
        </span>
        <span class={clsx([
            "text-lg",
            "font-medium",
            "text-gray-600",
        ])}>
            {uniqueRespondents}% unique respondents
        </span>
    </div>

    <!-- Questions -->
    <div class={clsx([
        "mt-4",
    ])}>
        <div class={clsx([
            "text-sm",
            "text-gray-600",
            "mb-2",
        ])}>
            Questions:
        </div>
        <div class={clsx([
            "flex",
            "flex-wrap",
            "gap-1",
        ])}>
            {#each questions as question}
                <span class={clsx([
                    "inline-block",
                    "bg-gray-100",
                    "text-gray-700",
                    "text-sm",
                    "px-2",
                    "py-1",
                    "rounded",
                    "font-medium",
                ])}>
                    {question}
                </span>
            {/each}
        </div>
    </div>
</div>