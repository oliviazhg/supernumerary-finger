import React, { useRef } from "react";
import { useGLTF } from "@react-three/drei";
import { useFrame } from "@react-three/fiber";

export default function FingerModel({ angles, ...props }) {
  const { nodes, materials } = useGLTF("/Finger_Assembly_4.1_2.glb");

  const joint1 = useRef();
  const joint2 = useRef();
  const joint3 = useRef();

  useFrame(() => {
    // If it rotates on the wrong axis, change .y to .x or .z
    if (joint1.current) joint1.current.rotation.x = angles.j1;
    if (joint2.current) joint2.current.rotation.x = angles.j2;
    if (joint3.current) joint3.current.rotation.x = angles.j3;
  });

  return (
    <group {...props} dispose={null}>
      <group ref={joint1} rotation={[Math.PI / 2, 0, 0]}>
        <mesh
          castShadow
          receiveShadow
          geometry={nodes.Body2001.geometry}
          material={materials["Steel - Satin"]}
          scale={10}
        />

        <group ref={joint2} position={[0, 46, 0]}>
          <mesh
            castShadow
            receiveShadow
            geometry={nodes.Body2.geometry}
            material={materials["Steel - Satin"]}
            scale={10}
          />

          <group ref={joint3} position={[0, 22, 0]}>
            <mesh
              castShadow
              receiveShadow
              geometry={nodes.Body1.geometry}
              material={materials["Steel - Satin"]}
              scale={10}
            />
          </group>
        </group>
      </group>
    </group>
  );
}

useGLTF.preload("/Finger_Assembly_4.1_2.glb");
