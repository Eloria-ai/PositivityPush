import { AnnouncementBar } from "@/components/announcement-bar"
import { Header } from "@/components/header"
import { HeroProductSection } from "@/components/hero-product-section"
import { SayGoodbyeSection } from "@/components/say-goodbye-section"
import { WhyChooseSection } from "@/components/why-choose-section"
import { HowItWorksSteps } from "@/components/how-it-works-steps"
import { SocialProofSection } from "@/components/social-proof-section"
import { FaqSection } from "@/components/faq-section"
import { Footer } from "@/components/footer"

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      <AnnouncementBar />
      <Header />
      <HeroProductSection />
      <SayGoodbyeSection />
      <WhyChooseSection />
      <HowItWorksSteps />
      <SocialProofSection />
      <FaqSection />
      <Footer />
    </div>
  )
}
