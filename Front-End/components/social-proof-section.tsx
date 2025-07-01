"use client"

import { Button } from "@/components/ui/button"

export function SocialProofSection() {
  const scrollToPricing = () => {
    const isMobile = window.innerWidth < 1024 // Tailwind's 'lg' breakpoint
    const targetId = isMobile ? "pricing-mobile" : "pricing-desktop"
    const pricingSection = document.getElementById(targetId)
    if (pricingSection) {
      pricingSection.scrollIntoView({ behavior: "smooth" })
    }
  }

  return (
    <section className="bg-white py-16">
      <div className="max-w-7xl mx-auto px-4">
        <div className="max-w-4xl mx-auto space-y-6">
          <h2 className="text-4xl font-bold text-gray-900 text-center">🔬 Studies Behind Positivity Push</h2>

          <div className="space-y-6">
            <div className="space-y-1">
              <div className="flex items-center space-x-4">
                <div className="w-16 h-16 bg-pink-100 rounded-full flex items-center justify-center">
                  <span className="text-2xl font-bold text-[#00C48C]">93%</span>
                </div>
                <p className="text-lg text-gray-600">
                  saw negative self-talk turn positive after 14 days of daily affirmations
                </p>
              </div>
              <p className="text-sm text-gray-500 ml-16">— University of Pennsylvania, 2021</p>
            </div>

            <div className="space-y-1">
              <div className="flex items-center space-x-4">
                <div className="w-16 h-16 bg-pink-100 rounded-full flex items-center justify-center">
                  <span className="text-2xl font-bold text-[#00C48C]">88%</span>
                </div>
                <p className="text-lg text-gray-600">
                  felt happier and calmer after a nightly gratitude note for 3 weeks
                </p>
              </div>
              <p className="text-sm text-gray-500 ml-16">— UC Davis, 2003</p>
            </div>

            <div className="space-y-1">
              <div className="flex items-center space-x-4">
                <div className="w-16 h-16 bg-pink-100 rounded-full flex items-center justify-center">
                  <span className="text-2xl font-bold text-[#00C48C]">76%</span>
                </div>
                <p className="text-lg text-gray-600">
                  hit weekly goals when they checked in with an accountability partner
                </p>
              </div>
              <p className="text-sm text-gray-500 ml-16">— ASTD Accountability Study, 2010</p>
            </div>
          </div>

          <div className="border-l-4 border-[#00C48C] bg-gray-50 pl-4 py-3">
            <p className="text-gray-700 text-base italic">
              We've baked these findings into every affirmation, gratitude prompt, and accountability nudge inside
              Positivity Push—so your progress is grounded in proven psychology, not guesswork.
            </p>
          </div>

          <div className="text-center">
            <Button
              onClick={scrollToPricing}
              className="bg-[#00C48C] hover:bg-[#00A876] text-white font-bold px-8 py-4 rounded-xl text-lg"
            >
              💖 I'M READY TO FEEL BETTER ➜
            </Button>
          </div>
        </div>
      </div>
    </section>
  )
}
