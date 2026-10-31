<script lang="ts">
  let {
    label,
    src,
    onclose,
  }: { label: string; src: string; onclose: () => void } = $props();
  function open(dialog: HTMLDialogElement) {
    dialog.showModal();
  }
</script>

<dialog
  use:open
  {onclose}
  onpointerdown={(event) => {
    if (event.target !== event.currentTarget) return;
    const bounds = event.currentTarget.getBoundingClientRect();
    if (
      event.clientX < bounds.left ||
      event.clientX > bounds.right ||
      event.clientY < bounds.top ||
      event.clientY > bounds.bottom
    )
      event.currentTarget.close();
  }}
  aria-labelledby="interaction-title"
>
  <h3
    id="interaction-title"
    class="has-text-white p-3 is-size-5 has-text-centered has-text-weight-bold"
  >
    Interaction: {label}
  </h3>
  <video {src} aria-label={label} controls autoplay muted playsinline></video>
  <form method="dialog"><button class="button is-light">Close</button></form>
</dialog>

<style>
  dialog {
    border: 0;
    padding: 0;
    width: 80%;
    max-width: 800px;
    max-height: 90vh;
    border-radius: 12px;
    background: #000;
  }
  dialog::backdrop {
    background: rgba(10, 10, 10, 0.86);
  }
  h3 {
    background: #1e293b;
    margin: 0;
  }
  video {
    width: 100%;
    max-height: 70vh;
    display: block;
  }
  form {
    padding: 0.75rem;
    text-align: right;
  }
</style>
