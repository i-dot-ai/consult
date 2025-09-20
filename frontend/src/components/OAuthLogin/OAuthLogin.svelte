<script lang="ts">
    export let errorMessage: string | null = null;
    
    let error: string | null = errorMessage;
</script>

<div class="govuk-!-margin-bottom-6">
    <h1 class="govuk-heading-l">Sign in</h1>
    
    {#if error}
        <div class="govuk-error-summary" role="alert" aria-labelledby="error-summary-title" tabindex="-1">
            <h2 class="govuk-error-summary__title" id="error-summary-title">
                There is a problem
            </h2>
            <div class="govuk-error-summary__body">
                <p>{error}</p>
            </div>
        </div>
    {/if}
    
    <p class="govuk-body">Use your government account to sign in to the consultation analyser.</p>
    
    <a 
        href="/auth/login"
        class="govuk-button"
        role="button"
        draggable="false"
        data-module="govuk-button"
    >
        <b>Sign in</b>
    </a>
</div>

