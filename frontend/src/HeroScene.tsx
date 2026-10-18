import { useEffect, useRef } from "react";
import * as THREE from "three";

const colors = [0xd9a441, 0xe0457b, 0x9b7bff, 0x3fb8af, 0x5a9bf6, 0xb5cf4a];

export default function HeroScene() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x0f1e24, 1);

    const scene = new THREE.Scene();
    scene.fog = new THREE.Fog(0x0f1e24, 22, 48);
    const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 100);
    scene.add(new THREE.AmbientLight(0xa9c3c9, 0.55));
    const sun = new THREE.DirectionalLight(0xffffff, 1.1);
    sun.position.set(7, 14, 8);
    scene.add(sun);

    const ground = new THREE.Mesh(
      new THREE.PlaneGeometry(28, 28),
      new THREE.MeshStandardMaterial({ color: 0x132a31, roughness: 0.95 }),
    );
    ground.rotation.x = -Math.PI / 2;
    scene.add(ground);
    const grid = new THREE.GridHelper(28, 28, 0x2a4a52, 0x1b343b);
    grid.position.y = 0.02;
    scene.add(grid);

    const river = new THREE.Mesh(
      new THREE.PlaneGeometry(28, 1.5),
      new THREE.MeshStandardMaterial({ color: 0x1a4b66, roughness: 0.25, metalness: 0.3 }),
    );
    river.rotation.x = -Math.PI / 2;
    river.position.set(0, 0.03, 2.5);
    scene.add(river);

    const blockGeometry = new THREE.BoxGeometry(1, 1, 1);
    const blockMaterials = [0x1f3d46, 0x264a53, 0x2e5761, 0x365f68].map(
      (color) => new THREE.MeshStandardMaterial({ color, roughness: 0.85 }),
    );
    const random = (seed: number) => {
      let value = seed;
      return () => {
        value = (value * 16807) % 2147483647;
        return value / 2147483647;
      };
    };
    const next = random(42);
    const dumpSpots = [-5, -2, 2, 5].flatMap((x, index) => [[x, index % 2 ? 4 : -4, index]]);
    const occupied = new Set(dumpSpots.map(([x, z]) => `${x}:${z}`));
    for (let x = -7; x <= 7; x += 1) {
      for (let z = -7; z <= 7; z += 1) {
        if (x % 3 === 0 || z % 3 === 0 || occupied.has(`${x}:${z}`) || next() < 0.18) continue;
        const height = 0.3 + next() ** 2 * 3.5;
        const block = new THREE.Mesh(blockGeometry, blockMaterials[Math.floor(next() * blockMaterials.length)]);
        block.scale.set(0.82, height, 0.82);
        block.position.set(x, height / 2, z);
        scene.add(block);
      }
    }

    const dumps = dumpSpots.map(([x, z, index]) => {
      const color = new THREE.Color(colors[index % colors.length]);
      const material = new THREE.MeshStandardMaterial({ color, roughness: 0.9, emissive: color, emissiveIntensity: 0.2 });
      const mound = new THREE.Mesh(new THREE.DodecahedronGeometry(0.45, 0), material);
      mound.scale.set(1.2, 0.45, 1);
      mound.position.set(x, 0.18, z);
      scene.add(mound);
      const ring = new THREE.Mesh(
        new THREE.RingGeometry(0.55, 0.66, 48),
        new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.8, side: THREE.DoubleSide, depthWrite: false }),
      );
      ring.rotation.x = -Math.PI / 2;
      ring.position.set(x, 0.05, z);
      scene.add(ring);
      return { x, z, ring, material, phase: index / 5 };
    });

    const satellite = new THREE.Group();
    const body = new THREE.Mesh(new THREE.BoxGeometry(0.6, 0.6, 0.9), new THREE.MeshStandardMaterial({ color: 0xd8dfe2, metalness: 0.6, roughness: 0.3 }));
    const solarMaterial = new THREE.MeshStandardMaterial({ color: 0x2f5fa8, metalness: 0.4, roughness: 0.35, emissive: 0x0b2448 });
    const panel = new THREE.Mesh(new THREE.BoxGeometry(1.9, 0.04, 0.72), solarMaterial);
    panel.position.x = 1.3;
    const otherPanel = panel.clone();
    otherPanel.position.x = -1.3;
    const sensor = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.18, 0.25, 20), new THREE.MeshStandardMaterial({ color: 0x4cc3b8, emissive: 0x4cc3b8, emissiveIntensity: 0.8 }));
    sensor.position.y = -0.4;
    satellite.add(body, panel, otherPanel, sensor);
    scene.add(satellite);

    const beam = new THREE.Mesh(new THREE.ConeGeometry(2, 10, 48, 1, true), new THREE.MeshBasicMaterial({ color: 0x7fe0d6, transparent: true, opacity: 0.07, side: THREE.DoubleSide, depthWrite: false, blending: THREE.AdditiveBlending }));
    scene.add(beam);
    const scanFoot = new THREE.Mesh(new THREE.RingGeometry(1.8, 2, 64), new THREE.MeshBasicMaterial({ color: 0x9af0e7, transparent: true, opacity: 0.55, side: THREE.DoubleSide, depthWrite: false }));
    scanFoot.rotation.x = -Math.PI / 2;
    scanFoot.position.y = 0.05;
    scene.add(scanFoot);

    let animationFrame = 0;
    const startedAt = performance.now();
    const resize = () => {
      const width = canvas.clientWidth || 800;
      const height = canvas.clientHeight || 500;
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
    };
    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(canvas);

    const frame = (now: number) => {
      const time = reducedMotion ? 8 : (now - startedAt) / 1000;
      const theta = reducedMotion ? 0.72 : time * 0.08;
      camera.position.set(20 * Math.sin(0.9) * Math.cos(theta), 15, 20 * Math.sin(0.9) * Math.sin(theta));
      camera.lookAt(0, 0, 0);
      const satelliteX = 6.5 * Math.sin(time * 0.23);
      const satelliteZ = 6 * Math.sin(time * 0.31 + 1);
      satellite.position.set(satelliteX, 10, satelliteZ);
      satellite.rotation.y = Math.atan2(6.5 * 0.23 * Math.cos(time * 0.23), 6 * 0.31 * Math.cos(time * 0.31 + 1));
      beam.position.set(satelliteX, 5, satelliteZ);
      scanFoot.position.x = satelliteX;
      scanFoot.position.z = satelliteZ;
      dumps.forEach((dump) => {
        const distance = Math.hypot(dump.x - satelliteX, dump.z - satelliteZ);
        const hit = distance < 2 ? 1 : 0;
        const pulse = (time * 0.7 + dump.phase) % 1;
        dump.ring.scale.setScalar(1 + pulse * (1.2 + hit * 1.8));
        dump.ring.material.opacity = (1 - pulse) * (0.35 + hit * 0.65);
        dump.material.emissiveIntensity = 0.2 + hit * 0.9;
      });
      renderer.render(scene, camera);
      if (!reducedMotion) animationFrame = requestAnimationFrame(frame);
    };
    resize();
    frame(performance.now());
    return () => { cancelAnimationFrame(animationFrame); resizeObserver.disconnect(); renderer.dispose(); };
  }, []);

  return <canvas ref={canvasRef} className="hero-canvas" aria-label="Animated 3D satellite scanning a city grid" />;
}
