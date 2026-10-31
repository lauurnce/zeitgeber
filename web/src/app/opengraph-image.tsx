import { ImageResponse } from "next/og";

import { site } from "@/lib/site";

export const alt = "Zeitgeber: set your body clock, not just your alarm.";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpenGraphImage() {
  return new ImageResponse(
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        padding: "72px 80px",
        color: "#eef0fa",
        background: "linear-gradient(180deg, #070a1c 0%, #0b1026 55%, #3b2a5c 100%)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 20, fontSize: 36 }}>
        <div
          style={{
            width: 56,
            height: 56,
            borderRadius: 28,
            border: "8px solid #f2b25c",
            borderLeftColor: "#5aa2ff",
            borderBottomColor: "#5aa2ff",
          }}
        />
        {site.name}
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
        <div style={{ fontSize: 76, fontWeight: 700, lineHeight: 1.1, maxWidth: 980 }}>
          Set your body clock, not just your alarm.
        </div>
        <div style={{ fontSize: 32, color: "#b6bbd6", maxWidth: 940 }}>
          A free body-clock planner for night-shift workers, built on published models.
        </div>
      </div>
      <div style={{ fontSize: 26, color: "#f2b25c" }}>
        Light, sleep and caffeine timing for 14 days
      </div>
    </div>,
    size,
  );
}
