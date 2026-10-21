import { Canvas, useFrame } from "@react-three/fiber";
import { useRef } from "react";

// Built from primitives, so there is no model file to download and it appears instantly.
function Plant() {
  const group = useRef();
  useFrame((_, dt) => {
    if (group.current) group.current.rotation.y += dt * 0.6;
  });
  const leaves = [
    { pos: [0.18, 0.7, 0], rot: [0, 0, -0.7] },
    { pos: [-0.18, 0.95, 0.05], rot: [0, 0, 0.7] },
    { pos: [0.12, 1.2, -0.05], rot: [0.2, 0, -0.5] },
  ];
  return (
    <group ref={group} position={[0, -0.6, 0]}>
      <mesh position={[0, 0.5, 0]}>
        <cylinderGeometry args={[0.03, 0.04, 1.1, 12]} />
        <meshStandardMaterial color="#2f7d5b" />
      </mesh>
      {leaves.map((l, i) => (
        <mesh key={i} position={l.pos} rotation={l.rot}>
          <sphereGeometry args={[0.22, 16, 12, 0, Math.PI * 2, 0, Math.PI / 2]} />
          <meshStandardMaterial color="#4fbf8f" side={2} />
        </mesh>
      ))}
    </group>
  );
}

export default function PlantLoader({ label = "Growing your curve\u2026" }) {
  return (
    <div className="plant-wrap" role="status" aria-live="polite">
      <Canvas camera={{ position: [0, 0.8, 2.6], fov: 40 }}>
        <ambientLight intensity={0.9} />
        <directionalLight position={[2, 3, 2]} intensity={0.8} />
        <Plant />
      </Canvas>
      <p style={{ textAlign: "center", marginTop: 4 }}>{label}</p>
    </div>
  );
}