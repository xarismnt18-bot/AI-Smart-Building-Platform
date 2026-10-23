import { useEffect, useMemo, useRef, useState } from "react";
import { useFrame } from "@react-three/fiber";
import { Html } from "@react-three/drei";
import * as THREE from "three";
import { SENSOR_POS } from "./layout";

// The radar only says "someone is here", not where: the figure stands beside
// the bed, at the back of the room, where the walls and desk don't hide it.
const SPOT = new THREE.Vector3(-3.0, 0, -3.0);
const HEIGHT = 1.42;                       // walls are 1.5 m tall in the model
const HOLO = new THREE.Color("#7DE3FF");
const IDLE = new THREE.Color("#3B5568");

/* ---------- hologram material: fresnel rim, moving scanlines, build-up from the floor ---------- */
const holoVertex = `
  varying vec3 vN; varying vec3 vV; varying float vY;
  void main(){
    vec4 world = modelMatrix * vec4(position, 1.);
    vY = world.y;
    vec4 mv = viewMatrix * world;
    vN = normalize(normalMatrix * normal); vV = normalize(-mv.xyz);
    gl_Position = projectionMatrix * mv;
  }`;
const holoFragment = `
  uniform vec3 uColor; uniform float uTime; uniform float uCut; uniform float uFade;
  varying vec3 vN; varying vec3 vV; varying float vY;
  void main(){
    if (vY > uCut) discard;
    float rim = pow(1. - abs(dot(vN, vV)), 2.2);
    float scan = .55 + .45 * smoothstep(.35, .5, abs(fract(vY * 22. - uTime * 1.6) - .5));
    float edge = smoothstep(.06, 0., uCut - vY);           // bright band where it is being built
    float flicker = .93 + .07 * sin(uTime * 37.);
    float a = min(1., (.55 + .6 * rim) * scan * flicker + edge);
    gl_FragColor = vec4(uColor * (.8 + rim * .35) + vec3(edge * .8), a * uFade);  // stays cyan under bloom
  }`;

function useHoloMaterial() {
  return useMemo(() => new THREE.ShaderMaterial({
    uniforms: { uColor: { value: HOLO.clone() }, uTime: { value: 0 }, uCut: { value: 0 }, uFade: { value: 0 } },
    vertexShader: holoVertex,
    fragmentShader: holoFragment,
    transparent: true,
    depthWrite: false,   // normal blending keeps it cyan even over a red (alert) room
  }), []);
}

/** Simple human made of capsules; `breath` scales the chest. */
function Figure({ material, chest, head }) {
  const limb = (r, len, pos, rotZ = 0, key) => (
    <mesh key={key} position={pos} rotation-z={rotZ} material={material}>
      <capsuleGeometry args={[r, len, 6, 14]} />
    </mesh>
  );
  return (
    <group scale={HEIGHT / 1.75}>
      <mesh ref={head} position-y={1.6} material={material}><sphereGeometry args={[0.13, 24, 18]} /></mesh>
      <group ref={chest} position-y={1.12}>
        <mesh material={material}><capsuleGeometry args={[0.17, 0.4, 8, 18]} /></mesh>
      </group>
      {limb(0.05, 0.5, [-0.27, 1.07, 0], 0.12, "la")}
      {limb(0.05, 0.5, [0.27, 1.07, 0], -0.12, "ra")}
      {limb(0.07, 0.62, [-0.1, 0.42, 0], 0.03, "ll")}
      {limb(0.07, 0.62, [0.1, 0.42, 0], -0.03, "rl")}
    </group>
  );
}

/* ---------- radar fan from the sensor into the room ---------- */
const fanVertex = `varying vec2 vP; void main(){ vP = position.xy; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.); }`;
const fanFragment = `
  uniform vec3 uColor; uniform float uTime; uniform float uLevel; uniform float uRange;
  varying vec2 vP;
  void main(){
    float r = length(vP) / uRange;
    float waves = smoothstep(.12, 0., abs(fract(r * 4. - uTime * .9) - .5) - .38);
    float fade = 1. - smoothstep(.55, 1., r);
    gl_FragColor = vec4(uColor, (.05 + .35 * waves) * fade * uLevel);
  }`;

const FAN_RANGE = 3.6;
const FAN_DIR = Math.atan2(-(SPOT.z - SENSOR_POS.z), SPOT.x - SENSOR_POS.x); // floor angle towards the spot

function RadarFan({ level, reduced }) {
  const mat = useRef();
  const uniforms = useMemo(() => ({
    uColor: { value: HOLO.clone() }, uTime: { value: 0 }, uLevel: { value: 0.3 }, uRange: { value: FAN_RANGE },
  }), []);
  useFrame(({ clock }) => {
    if (!mat.current) return;
    if (!reduced) mat.current.uniforms.uTime.value = clock.elapsedTime;
    mat.current.uniforms.uLevel.value = 0.25 + 0.75 * level.current;
    mat.current.uniforms.uColor.value.copy(IDLE).lerp(HOLO, level.current);
  });
  return (
    <mesh position={[SENSOR_POS.x, 0.03, SENSOR_POS.z]} rotation-x={-Math.PI / 2} raycast={() => null}>
      <circleGeometry args={[FAN_RANGE, 48, FAN_DIR - 0.6, 1.2]} />
      <shaderMaterial ref={mat} uniforms={uniforms} vertexShader={fanVertex} fragmentShader={fanFragment}
        transparent depthWrite={false} blending={THREE.AdditiveBlending} side={THREE.DoubleSide} />
    </mesh>
  );
}

/* ---------- label: how long someone has been in ---------- */
function minutesText(since) {
  if (!since) return "Detected";
  const min = Math.max(0, Math.floor((Date.now() / 1000 - since) / 60));
  if (min < 1) return "Just came in";
  if (min < 60) return `In the room · ${min} min`;
  const h = Math.floor(min / 60);
  return `In the room · ${h} h ${min % 60} min`;
}

function StayLabel({ since }) {
  const [, tick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => tick((n) => n + 1), 20000);
    return () => clearInterval(id);
  }, []);
  return (
    <Html position={[0, HEIGHT + 0.32, 0]} center distanceFactor={9} zIndexRange={[20, 0]} style={{ pointerEvents: "none" }}>
      <div className="imm-person-tag"><span aria-hidden="true" />{minutesText(since)}</div>
    </Html>
  );
}

/**
 * Someone in the live room: a hologram that builds up from the floor when the
 * radar sees a person and dissolves when the room is empty, a detection ripple,
 * a beam from the radar and the radar's field on the floor.
 */
export function Presence({ present, since, reduced }) {
  const material = useHoloMaterial();
  const level = useRef(present ? 1 : 0);
  const body = useRef();
  const chest = useRef();
  const ripple = useRef();
  const rippleRing = useRef();
  const rippleAt = useRef(-10);
  const beam = useRef();
  const halo = useRef();
  const head = useRef();
  const wasPresent = useRef(present);

  useEffect(() => {
    if (present && !wasPresent.current) rippleAt.current = performance.now() / 1000;
    wasPresent.current = present;
  }, [present]);

  useEffect(() => () => material.dispose(), [material]);

  useFrame(({ clock, invalidate }, dt) => {
    const t = clock.elapsedTime;
    const target = present ? 1 : 0;
    level.current = reduced ? target
      : THREE.MathUtils.damp(level.current, target, present ? 1.6 : 2.4, Math.min(dt, 0.05));
    const k = level.current;
    const u = head.current?.material.uniforms;   // shared by all the body parts
    if (!u) return;
    u.uTime.value = reduced ? 0 : t;
    u.uCut.value = k * (HEIGHT + 0.1) - 0.02;      // builds from the floor up, dissolves top-down
    u.uFade.value = Math.min(1, k * 1.6);
    if (body.current) {
      body.current.visible = k > 0.01;
      body.current.rotation.y = reduced ? 0.5 : 0.5 + Math.sin(t * 0.35) * 0.25;  // slowly looks around
    }
    if (chest.current) chest.current.scale.set(1 + (reduced ? 0 : Math.sin(t * 1.5) * 0.035), 1, 1 + (reduced ? 0 : Math.sin(t * 1.5) * 0.05));
    if (halo.current) halo.current.opacity = k * (reduced ? 0.4 : 0.3 + 0.15 * Math.sin(t * 2.4));
    if (beam.current) beam.current.opacity = k * (reduced ? 0.5 : 0.35 + 0.25 * Math.sin(t * 6));
    if (ripple.current && rippleRing.current) {
      const age = performance.now() / 1000 - rippleAt.current;
      const on = !reduced && age < 1.8;
      rippleRing.current.visible = on;
      if (on) {
        rippleRing.current.scale.setScalar(0.3 + age * 2.4);
        ripple.current.opacity = 0.8 * (1 - age / 1.8);
      }
    }
    if (reduced && Math.abs(k - target) > 0.001) invalidate();
  });

  const beamLine = useMemo(() => {
    const geo = new THREE.BufferGeometry().setFromPoints([SENSOR_POS.clone(), new THREE.Vector3(SPOT.x, HEIGHT * 0.72, SPOT.z)]);
    const mat = new THREE.LineBasicMaterial({
      color: HOLO, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false,
    });
    return new THREE.Line(geo, mat);
  }, []);
  useEffect(() => {
    beam.current = beamLine.material;
    return () => {
      beamLine.geometry.dispose();
      beamLine.material.dispose();
    };
  }, [beamLine]);

  return (
    <group raycast={() => null}>
      <RadarFan level={level} reduced={reduced} />
      <primitive object={beamLine} />
      <group position={SPOT.toArray()}>
        <group ref={body}>
          <Figure material={material} chest={chest} head={head} />
        </group>
        <mesh rotation-x={-Math.PI / 2} position-y={0.02}>
          <ringGeometry args={[0.3, 0.42, 48]} />
          <meshBasicMaterial ref={halo} color={HOLO} transparent opacity={0} depthWrite={false}
            blending={THREE.AdditiveBlending} side={THREE.DoubleSide} />
        </mesh>
        <group ref={rippleRing} visible={false}>
          <mesh rotation-x={-Math.PI / 2} position-y={0.04}>
            <ringGeometry args={[0.46, 0.5, 64]} />
            <meshBasicMaterial ref={ripple} color={HOLO} transparent opacity={0} depthWrite={false}
              blending={THREE.AdditiveBlending} side={THREE.DoubleSide} />
          </mesh>
        </group>
        {present && <StayLabel since={since} />}
      </group>
    </group>
  );
}

