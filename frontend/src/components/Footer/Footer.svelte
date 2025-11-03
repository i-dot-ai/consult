<script lang="ts">
  import clsx from "clsx";

  import AnnounceIcon from "../svg/AnnounceIcon.svelte";
  import IaiIcon from "../svg/IaiIcon.svelte";
  import OglIcon from "../svg/OglIcon.svelte";
  import { getBackendUrl } from "../../global/utils";


  let version = { sha: "unknown" };

  fetch(`${getBackendUrl()}/api/git-sha/`, {method: "GET"})
    .then(response => response.json())
    .then(data => {
      version = data;
    })
    .catch(() => {
      version = { sha: "unknown" };
    });


</script>

<footer class={clsx(["py-6", "px-0", "bg-black", "text-white", "text-xs"])}>
  <div class="mx-6">
    <div>
      <a class="flex items-center" href="https://ai.gov.uk">
        <IaiIcon />
      </a>
      <div>
        <ul class={clsx(["flex", "flex-wrap", "gap-2", "my-2", "mx-0", "p-0"])}>
          <li>
            <a data-testid="privacy-link" href="/privacy/">Privacy notice</a>
          </li>
          <li>
            <a href="https://github.com/i-dot-ai/consultation-analyser"
              >Version:{version.sha}</a
            >
          </li>
        </ul>
        <div class={clsx(["flex", "items-center", "gap-2", "mt-4", "text-sm"])}>
          <OglIcon />
          <span class="text-white">
            All content is available under the
            <a
              href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
              rel="license">Open Government Licence v3.0</a
            >, except where otherwise stated
          </span>
        </div>
      </div>
    </div>
    <div class={clsx(["flex", "items-center", "gap-2", "mt-4"])}>
      <AnnounceIcon />
      <span
        >This is a new service your&nbsp;<a
          href="https://www.smartsurvey.co.uk/s/GESFSF/">feedback</a
        >
        will help us to <span>improve it</span></span
      >
    </div>
  </div>
</footer>
