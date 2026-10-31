import { HowItWorks } from "@/components/landing/HowItWorks";
import { Hero } from "@/components/landing/Hero";
import { Limitations } from "@/components/landing/Limitations";
import { LivePreview } from "@/components/landing/LivePreview";
import { Problem } from "@/components/landing/Problem";
import { Science } from "@/components/landing/Science";
import { SiteFooter } from "@/components/landing/SiteFooter";
import { Story } from "@/components/landing/Story";

export default function Home() {
  return (
    <>
      <Hero />
      <main>
        <Story />
        <Problem />
        <HowItWorks />
        <LivePreview />
        <Science />
        <Limitations />
      </main>
      <SiteFooter />
    </>
  );
}
