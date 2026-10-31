import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

import type { Manifest, Point, ContactKey } from "#lib/data/spacetime.js";

// A stack of real image planes, rather than a density reconstruction.
// Optional tracks are demo-only optical-flow estimates, constrained at annotated endpoints.
export async function createScene(host: HTMLElement, data: Manifest) {
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.domElement.setAttribute(
    "aria-label",
    "Video frames arranged through time. Drag to rotate. Pinch or hold Ctrl while scrolling to zoom; zoom buttons are also available.",
  );
  renderer.domElement.setAttribute("role", "img");
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(36, 1, 0.1, 100);
  const controls = new OrbitControls(camera, renderer.domElement);
  // OrbitControls defaults to touch-action:none. Keep vertical page scrolling
  // available on phones; horizontal drags can still rotate the volume.
  renderer.domElement.style.touchAction = "pan-y";
  controls.enablePan = false;
  controls.enableZoom = true;
  controls.minDistance = 4;
  // Let ordinary wheel events scroll the page. Ctrl+wheel also covers trackpad
  // pinch gestures; OrbitControls handles those and two-finger touch pinches.
  const routeWheel = (event: WheelEvent) => {
    if (!event.ctrlKey) event.stopImmediatePropagation();
  };
  renderer.domElement.addEventListener("wheel", routeWheel, {
    capture: true,
    passive: true,
  });
  controls.minPolarAngle = Math.PI * 0.18;
  controls.maxPolarAngle = Math.PI * 0.82;
  const width = 3.6;
  const height = (width * data.height) / data.width;
  const depth = 4.8;
  const z = (frame: number) =>
    depth / 2 - ((frame - data.first) / (data.contact - data.first)) * depth;
  const textures: THREE.Texture[] = [];
  const geometries: THREE.BufferGeometry[] = [];
  const materials: THREE.Material[] = [];
  let disposed = false;
  let opacity = 0.12;
  let slice = data.observation;
  const render = () => {
    if (!disposed) renderer.render(scene, camera);
  };
  const cleanup = () => {
    disposed = true;
    observer.disconnect();
    renderer.domElement.removeEventListener("wheel", routeWheel, true);
    controls.dispose();
    textures.forEach((texture) => texture.dispose());
    geometries.forEach((geometry) => geometry.dispose());
    materials.forEach((material) => material.dispose());
    renderer.dispose();
    renderer.domElement.remove();
  };
  const resize = () => {
    if (!host.clientWidth || !host.clientHeight) return;
    const aspect = host.clientWidth / host.clientHeight;
    renderer.setSize(host.clientWidth, host.clientHeight, false);
    camera.aspect = aspect;
    camera.updateProjectionMatrix();
    render();
  };
  const observer = new ResizeObserver(resize);
  try {
    const loader = new THREE.TextureLoader();
    // allSettled ensures successful textures are also disposed if another fails.
    const loaded = await Promise.allSettled(
      data.frames.map(async (frame) => {
        const texture = await loader.loadAsync(frame.src);
        texture.colorSpace = THREE.SRGBColorSpace;
        textures.push(texture);
        return texture;
      }),
    );
    const failure = loaded.find((result) => result.status === "rejected");
    if (failure) throw new Error("The video frames could not be loaded.");
    const plane = new THREE.PlaneGeometry(width, height);
    geometries.push(plane);
    const planes = data.frames.map((frame, index) => {
      const result = loaded[index] as PromiseFulfilledResult<THREE.Texture>;
      const material = new THREE.MeshBasicMaterial({
        map: result.value,
        side: THREE.DoubleSide,
        transparent: true,
        depthWrite: false,
      });
      materials.push(material);
      const mesh = new THREE.Mesh(plane, material);
      mesh.position.z = z(frame.index);
      scene.add(mesh);
      return { frame, material, mesh };
    });
    const pointAt = (point: Point, frame: number) =>
      new THREE.Vector3(
        (point.x / data.width - 0.5) * width,
        (0.5 - point.y / data.height) * height,
        z(frame) + 0.015,
      );
    const inspectedContacts: { key: ContactKey; mesh: THREE.Mesh }[] = [];
    for (const [key, color] of [
      ["contact_thumb", 0x39baff],
      ["contact_index", 0xf36ac4],
    ] as const) {
      const endpoints = [data.observation, data.contact].map((frame) =>
        pointAt(data.anchors[frame][key], frame),
      );
      const track = data.estimated_tracks?.paths[key];
      const path = track?.map((point) => pointAt(point, point.frame));
      // Smooth the measured-and-corrected path for display; do not add arbitrary bends.
      const curve = path
        ? new THREE.CatmullRomCurve3(path, false, "centripetal")
        : null;
      const geometry = new THREE.BufferGeometry().setFromPoints(
        curve ? curve.getPoints(160) : endpoints,
      );
      const material = new THREE.LineDashedMaterial({
        color,
        dashSize: 0.08,
        gapSize: 0.05,
        depthTest: false,
        depthWrite: false,
        transparent: true,
      });
      geometries.push(geometry);
      materials.push(material);
      const line = new THREE.Line(geometry, material);
      line.computeLineDistances();
      line.renderOrder = 10;
      scene.add(line);
      endpoints.forEach((position) => {
        const geometry = new THREE.SphereGeometry(0.06, 16, 12);
        const material = new THREE.MeshBasicMaterial({
          color,
          depthTest: false,
          depthWrite: false,
          transparent: true,
        });
        geometries.push(geometry);
        materials.push(material);
        const dot = new THREE.Mesh(geometry, material);
        dot.position.copy(position);
        dot.renderOrder = 11;
        scene.add(dot);
      });
      if (track) {
        const geometry = new THREE.RingGeometry(0.055, 0.075, 24);
        const material = new THREE.MeshBasicMaterial({
          color,
          side: THREE.DoubleSide,
          depthTest: false,
          depthWrite: false,
          transparent: true,
        });
        geometries.push(geometry);
        materials.push(material);
        const marker = new THREE.Mesh(geometry, material);
        marker.renderOrder = 12;
        marker.visible = false;
        scene.add(marker);
        inspectedContacts.push({ key, mesh: marker });
      }
    }
    const border = (frame: number, color: number) => {
      const geometry = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(-width / 2, -height / 2, 0),
        new THREE.Vector3(width / 2, -height / 2, 0),
        new THREE.Vector3(width / 2, height / 2, 0),
        new THREE.Vector3(-width / 2, height / 2, 0),
      ]);
      const material = new THREE.LineBasicMaterial({ color });
      geometries.push(geometry);
      materials.push(material);
      const outline = new THREE.LineLoop(geometry, material);
      outline.position.z = z(frame) + 0.02;
      scene.add(outline);
      return outline;
    };
    border(data.observation, 0xffffff);
    border(data.contact, 0x888888);
    const selected = border(slice, 0xffffff);
    const update = () => {
      for (const { frame, material, mesh } of planes) {
        const anchor =
          frame.index === data.observation || frame.index === data.contact;
        const current = frame.index === slice;
        // At zero only the two annotated image planes remain.
        material.opacity = anchor
          ? 1
          : current && opacity > 0
            ? Math.max(opacity, 0.7)
            : opacity;
        mesh.visible = anchor || opacity > 0;
      }
      selected.position.z = z(slice) + 0.025;
      selected.visible =
        opacity > 0 && slice !== data.observation && slice !== data.contact;
      for (const { key, mesh } of inspectedContacts) {
        const point = data.estimated_tracks?.paths[key].find(
          (point) => point.frame === slice,
        );
        mesh.visible = !!point && !point.annotated && opacity > 0;
        if (point) mesh.position.copy(pointAt(point, slice));
      }
      render();
    };
    const resetView = () => {
      const aspect = host.clientWidth / Math.max(host.clientHeight, 1);
      camera.position
        .set(7.5, 4.2, 8.5)
        .multiplyScalar(Math.max(1, 0.95 / aspect));
      controls.target.set(0, 0, 0);
      controls.maxDistance = camera.position.length() * 3;
      controls.update();
      render();
    };
    controls.addEventListener("change", render);
    host.append(renderer.domElement);
    observer.observe(host);
    resize();
    resetView();
    update();
    return {
      zoom(factor: number) {
        const offset = camera.position.clone().sub(controls.target);
        const distance = THREE.MathUtils.clamp(
          offset.length() * factor,
          controls.minDistance,
          controls.maxDistance,
        );
        camera.position.copy(controls.target).add(offset.setLength(distance));
        controls.update();
      },
      setOpacity(value: number) {
        opacity = value;
        update();
      },
      setSlice(value: number) {
        slice = data.frames[value].index;
        update();
      },
      focusAnchors: resetView,
      resetView,
      dispose: cleanup,
    };
  } catch (error) {
    cleanup();
    throw error;
  }
}
