<script lang="ts">
  import type { LayoutProps } from "./$types";
  import "#lib/styles/global.css";
  let { children }: LayoutProps = $props();
</script>

{@render children()}
