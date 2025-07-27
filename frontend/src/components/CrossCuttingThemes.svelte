<script lang="ts">
    import clsx from "clsx";
    import CrossCuttingThemeCard from "./CrossCuttingThemeCard.svelte";

    // Sample data with varying numbers of cards and questions to test layout flexibility
    const sampleThemes = [
        {
            title: "Healthcare AI Regulatory Standards",
            mentions: 1240,
            uniqueRespondents: 68.3,
            questions: ["Q1", "Q4", "Q11", "Q16"]
        },
        {
            title: "Financial Services Risk Management", 
            mentions: 1187,
            uniqueRespondents: 65.8,
            questions: ["Q1", "Q3", "Q5", "Q7", "Q9", "Q12", "Q15", "Q18", "Q21", "Q23"]
        },
        {
            title: "Data Security Architecture Standards",
            mentions: 1167,
            uniqueRespondents: 71.2,
            questions: ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "Q9", "Q10", "Q11", "Q12", "Q13", "Q14", "Q15", "Q16", "Q17", "Q18", "Q19", "Q20"]
        },
        {
            title: "Access Control Implementation Guidelines",
            mentions: 1089,
            uniqueRespondents: 63.4,
            questions: ["Q4", "Q12", "Q20", "Q25"]
        },
        {
            title: "Transportation Safety Protocols",
            mentions: 1045,
            uniqueRespondents: 59.7,
            questions: ["Q1", "Q16", "Q19", "Q21"]
        },
        {
            title: "Data Anonymisation Techniques",
            mentions: 1012,
            uniqueRespondents: 66.1,
            questions: ["Q2", "Q4", "Q8", "Q17"]
        },
        {
            title: "Privacy Framework Implementation",
            mentions: 890,
            uniqueRespondents: 72.1,
            questions: ["Q3", "Q9", "Q14"]
        },
        {
            title: "Compliance Monitoring Systems",
            mentions: 756,
            uniqueRespondents: 58.9,
            questions: ["Q5", "Q11", "Q18", "Q22"]
        }
    ];
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
            <!-- Cross-cutting themes icon (network/interconnected graph) -->
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
                    <!-- Central node -->
                    <circle cx="12" cy="12" r="2" fill="currentColor"/>
                    
                    <!-- Corner nodes -->
                    <circle cx="6" cy="6" r="1.5" fill="currentColor"/>
                    <circle cx="18" cy="6" r="1.5" fill="currentColor"/>
                    <circle cx="6" cy="18" r="1.5" fill="currentColor"/>
                    <circle cx="18" cy="18" r="1.5" fill="currentColor"/>
                    
                    <!-- Edge nodes -->
                    <circle cx="12" cy="4" r="1.5" fill="currentColor"/>
                    <circle cx="20" cy="12" r="1.5" fill="currentColor"/>
                    <circle cx="12" cy="20" r="1.5" fill="currentColor"/>
                    <circle cx="4" cy="12" r="1.5" fill="currentColor"/>
                    
                    <!-- Connection lines -->
                    <line x1="12" y1="10" x2="12" y2="4" stroke="currentColor" stroke-width="1.5" opacity="0.7"/>
                    <line x1="14" y1="12" x2="20" y2="12" stroke="currentColor" stroke-width="1.5" opacity="0.7"/>
                    <line x1="12" y1="14" x2="12" y2="20" stroke="currentColor" stroke-width="1.5" opacity="0.7"/>
                    <line x1="10" y1="12" x2="4" y2="12" stroke="currentColor" stroke-width="1.5" opacity="0.7"/>
                    
                    <!-- Diagonal connections -->
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
        {#each sampleThemes as theme}
            <CrossCuttingThemeCard
                title={theme.title}
                mentions={theme.mentions}
                uniqueRespondents={theme.uniqueRespondents}
                questions={theme.questions}
            />
        {/each}
    </div>
</div>