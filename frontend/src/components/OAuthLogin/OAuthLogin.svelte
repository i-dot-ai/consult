<script lang="ts">
    import { startOAuthLogin } from "../../lib/oauth";
    
    export let errorMessage: string | null = null;
    
    let isLoading = false;
    let error: string | null = errorMessage;
    
    async function handleOAuthLogin() {
        try {
            isLoading = true;
            error = null;
            await startOAuthLogin();
        } catch (err) {
            error = err instanceof Error ? err.message : 'Login failed';
            isLoading = false;
        }
    }
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
    
    <button 
        class="govuk-button govuk-button--start" 
        type="button" 
        on:click={handleOAuthLogin}
        disabled={isLoading}
    >
        {#if isLoading}
            Signing in...
        {:else}
            Sign in with government account
        {/if}
        
        {#if !isLoading}
            <svg class="govuk-button__start-icon" xmlns="http://www.w3.org/2000/svg" width="17.5" height="19" viewBox="0 0 33 40" aria-hidden="true" focusable="false">
                <path fill="currentColor" d="m0 0h13l20 20-20 20h-13v-8l13-12-13-12z"/>
            </svg>
        {/if}
    </button>
    
    <details class="govuk-details" data-module="govuk-details">
        <summary class="govuk-details__summary">
            <span class="govuk-details__summary-text">
                Help with signing in
            </span>
        </summary>
        <div class="govuk-details__text">
            <p>You need a government account to access the consultation analyser.</p>
            <p>If you don't have access or are having trouble signing in, contact your administrator.</p>
        </div>
    </details>
</div>

<style>
    .govuk-button:disabled {
        opacity: 0.7;
        cursor: not-allowed;
    }
</style>