import { Suspense, useMemo, useRef } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import { Bloom, EffectComposer } from "@react-three/postprocessing";
import { OptionalBoundary } from "../ui/OptionalBoundary";
import { homeView, roomView, ROOMS } from "./layout";
import { Apartment, CameraDirector, DataPath, Ground, LiveRoomEffects, RoomTags } from "./SceneParts";

const START = [34, 30, 38]; // far away; the intro flight swoops in from here

/**
 * Full-bleed 3D home. `liveColor` is null when the sensor has no data,
 * which renders the live room grey with no heat / particles.
 */
export default function ImmersiveScene({
  liveName, liveColor, liveText, view, focus, selected, onSelect, alert, packetSeq, status, reduced, narrow,
}) {
  const controls = useRef();
  const camView = useMemo(() => {
    const room = ROOMS.find((r) => r.id === focus);
    return room ? roomView(room, narrow) : homeView(narrow);
  }, [focus, narrow]);

  return (
    <Canvas
      className="imm-canvas"
      dpr={[1, 2]}
      frameloop={reduced ? "demand" : "always"}
      camera={{ fov: 38, near: 0.1, far: 200, position: reduced ? camView.position.toArray() : START }}
      aria-label="3D model of the home. Drag to orbit, scroll to zoom, click a room to focus it."
    >
      <color attach="background" args={["#04070C"]} />
      <fog attach="fog" args={["#04070C", narrow ? 50 : 30, narrow ? 90 : 62]} />
      <hemisphereLight args={["#7FB8E6", "#05080C", 0.55]} />
      <directionalLight position={[-10, 18, 8]} intensity={0.7} color="#BFD9F2" />

      <Ground reduced={reduced} />
      <Apartment liveColor={liveColor} alert={Boolean(alert)} reduced={reduced} selected={selected} onSelect={onSelect} xray={view === "xray"} />
      {liveColor && <LiveRoomEffects color={liveColor} view={view} alert={alert} reduced={reduced} />}
      <DataPath packetSeq={packetSeq} status={status} reduced={reduced} />
      <RoomTags liveName={liveName} liveText={liveText} liveHasData={Boolean(liveColor)} alert={Boolean(alert)} />

      <OrbitControls
        ref={controls}
        makeDefault
        enableDamping={!reduced}
        dampingFactor={0.06}
        minDistance={9}
        maxDistance={60}
        maxPolarAngle={1.32}
        autoRotate={!reduced && focus === "home"}
        autoRotateSpeed={0.35}
      />
      <CameraDirector view={camView} controls={controls} reduced={reduced} />

      <OptionalBoundary>
        <Suspense fallback={null}>
          <EffectComposer multisampling={0}>
            <Bloom mipmapBlur intensity={0.9} luminanceThreshold={0.18} luminanceSmoothing={0.2} />
          </EffectComposer>
        </Suspense>
      </OptionalBoundary>
    </Canvas>
  );
}
