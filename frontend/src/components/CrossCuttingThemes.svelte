<script lang="ts">
    import clsx from "clsx";
    import CrossCuttingThemeCard from "./CrossCuttingThemeCard.svelte";

    // TypeScript interfaces
    export interface CrossCuttingTheme {
        id: string;
        name: string;
        description: string;
        mentions: number;
        uniqueRespondents: number;
        questions: string[];
    }

    // Props
    export let themes: CrossCuttingTheme[] = [];
    export let loading: boolean = false;
</script>

<div class={clsx([
    "bg-gray-50",
    "border",
    "border-gray-200",
    "rounded-xl",
    "p-6",
    "mb-8",
])}>
    <!-- Header Section -->
    <div class={clsx([
        "flex",
        "items-center",
        "justify-between",
        "mb-6",
    ])}>
        <div class={clsx([
            "flex",
            "items-center",
            "gap-3",
        ])}>
            <!-- Network icon -->
            <div class={clsx([
                "w-8",
                "h-8",
                "bg-primary",
                "rounded",
                "flex",
                "items-center",
                "justify-center",
            ])}>
                <svg 
                    width="18" 
                    height="18" 
                    viewBox="0 0 24 24" 
                    fill="none" 
                    xmlns="http://www.w3.org/2000/svg"
                    class="text-white"
                >
                    <circle cx="12" cy="12" r="2" fill="currentColor"/>
                    <circle cx="6" cy="6" r="1.5" fill="currentColor"/>
                    <circle cx="18" cy="6" r="1.5" fill="currentColor"/>
                    <circle cx="6" cy="18" r="1.5" fill="currentColor"/>
                    <circle cx="18" cy="18" r="1.5" fill="currentColor"/>
                    <circle cx="12" cy="4" r="1.5" fill="currentColor"/>
                    <circle cx="20" cy="12" r="1.5" fill="currentColor"/>
                    <circle cx="12" cy="20" r="1.5" fill="currentColor"/>
                    <circle cx="4" cy="12" r="1.5" fill="currentColor"/>
                    <line x1="12" y1="10" x2="12" y2="4" stroke="currentColor" stroke-width="1.5" opacity="0.7"/>
                    <line x1="14" y1="12" x2="20" y2="12" stroke="currentColor" stroke-width="1.5" opacity="0.7"/>
                    <line x1="12" y1="14" x2="12" y2="20" stroke="currentColor" stroke-width="1.5" opacity="0.7"/>
                    <line x1="10" y1="12" x2="4" y2="12" stroke="currentColor" stroke-width="1.5" opacity="0.7"/>
                    <line x1="10.5" y1="10.5" x2="6" y2="6" stroke="currentColor" stroke-width="1.5" opacity="0.7"/>
                    <line x1="13.5" y1="10.5" x2="18" y2="6" stroke="currentColor" stroke-width="1.5" opacity="0.7"/>
                    <line x1="10.5" y1="13.5" x2="6" y2="18" stroke="currentColor" stroke-width="1.5" opacity="0.7"/>
                    <line x1="13.5" y1="13.5" x2="18" y2="18" stroke="currentColor" stroke-width="1.5" opacity="0.7"/>
                </svg>
            </div>
            
            <div>
                <h2 class={clsx([
                    "text-2xl",
                    "font-bold",
                    "text-gray-900",
                    "mb-1",
                ])}>
                    Cross cutting themes
                </h2>
                <p class={clsx([
                    "text-gray-600",
                    "text-sm",
                ])}>
                    Top themes mentioned across all consultation questions.
                </p>
            </div>
        </div>

        <!-- View Details Link -->
        <a 
            href="#" 
            class={clsx([
                "flex",
                "items-center",
                "gap-2",
                "text-primary",
                "font-medium",
                "hover:underline",
                "transition-colors",
                "duration-200",
            ])}
        >
            View details
            <svg 
                width="16" 
                height="16" 
                viewBox="0 0 16 16" 
                fill="none" 
                xmlns="http://www.w3.org/2000/svg"
                class="text-primary"
            >
                <path 
                    d="M6 12L10 8L6 4" 
                    stroke="currentColor" 
                    stroke-width="2" 
                    stroke-linecap="round" 
                    stroke-linejoin="round"
                />
            </svg>
        </a>
    </div>

    <!-- Cards Grid -->
    <div class={clsx([
        "grid",
        "grid-cols-1",
        "md:grid-cols-2",
        "lg:grid-cols-3",
        "gap-4",
    ])}>
        {#if loading}
            <div class="col-span-full flex items-center justify-center py-12">
                <div class="text-center">
                    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"></div>
                    <p class="text-gray-600">Loading cross-cutting themes...</p>
                </div>
            </div>
        {:else if themes.length === 0}
            <div class="col-span-full">
                <div class="text-center py-12">
                    <div class="text-gray-400 mb-2">
                        <svg class="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                        </svg>
                    </div>
                    <p class="text-gray-600 font-medium">No cross-cutting themes found</p>
                    <p class="text-gray-500 text-sm mt-1">Cross-cutting themes will appear here once they are created for this consultation.</p>
                </div>
            </div>
        {:else}
            {#each themes as theme}
                <CrossCuttingThemeCard
                    title={theme.name}
                    mentions={theme.mentions}
                    uniqueRespondents={theme.uniqueRespondents}
                    questions={theme.questions}
                />
            {/each}
        {/if}
    </div>
</div>