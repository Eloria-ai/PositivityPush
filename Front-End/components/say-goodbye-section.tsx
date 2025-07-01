"use client"

import { Button } from "@/components/ui/button"
import Image from "next/image"

export function SayGoodbyeSection() {
  const scrollToPricing = () => {
    const isMobile = window.innerWidth < 1024 // Tailwind's 'lg' breakpoint
    const targetId = isMobile ? "pricing-mobile" : "pricing-desktop"
    const pricingSection = document.getElementById(targetId)
    if (pricingSection) {
      pricingSection.scrollIntoView({ behavior: "smooth" })
    }
  }

  return (
    <section className="bg-gradient-to-br from-teal-50/60 to-emerald-50/60 py-16">
      <div className="max-w-7xl mx-auto px-4">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          {/* Left Column - Content */}
          <div className="space-y-8">
            {/* Main Headline */}
            <div className="space-y-4">
              <h2 className="text-3xl font-bold text-gray-900 leading-tight">
                What's the One Thing Holding You Back From The Life You Want?
              </h2>

              <div className="text-gray-600 text-lg">
                <p>It's not skill.</p>
                <p>It's not talent.</p>
                <p>It's not more time or even more knowledge.</p>
                <p>It's the negative voice inside you, whispering:</p>
              </div>

              <p className="text-gray-600 text-lg italic">
                "You can't do this. You're not enough. It is not gonna work."
              </p>

              <div className="space-y-1 text-gray-600 text-lg">
                <p className="font-semibold text-gray-900">But here's the truth:</p>
                <p>That voice isn't just holding you back—it's quietly stealing your dreams, piece by piece.</p>
              </div>
            </div>

            {/* Every Day You Wait Section */}
            <div className="space-y-4">
              <h3 className="text-2xl font-bold text-gray-900">Every Day You Wait, Your Dream Life Waits Too.</h3>

              <div className="space-y-1 text-gray-600 text-lg">
                <p>
                  The fulfilling career you've always wanted?{" "}
                  <span className="font-semibold text-gray-900">Still waiting.</span>
                </p>
                <p>
                  The confidence to walk into any room and own it?{" "}
                  <span className="font-semibold text-gray-900">Still waiting.</span>
                </p>
                <p>
                  A fit, healthy body you're proud of?{" "}
                  <span className="font-semibold text-gray-900">Still waiting.</span>
                </p>
                <p>
                  Inner peace, freedom, and authentic happiness?{" "}
                  <span className="font-semibold text-gray-900">Still waiting.</span>
                </p>
              </div>
            </div>

            {/* Be Honest Section */}
            <div className="space-y-4">
              <h3 className="text-2xl font-bold text-gray-900">Be Honest: Do You Feel Any of These?</h3>

              <div className="space-y-1 text-gray-600 text-lg">
                <p>Constantly postponing your goals, thinking "I'll start tomorrow" (but tomorrow never comes).</p>
                <p>Paralyzed by anxiety, self-doubt, and endless "what-ifs."</p>
                <p>Stuck in analysis paralysis, always thinking, rarely acting.</p>
                <p>Watching others succeed, grow, and thrive, while you're still exactly where you were last year.</p>
              </div>

              <div className="space-y-1 text-gray-600 text-lg pt-2">
                <p className="font-semibold text-gray-900">
                  If this feels familiar, your mind is the problem. And science says that your mind is also the
                  solution.
                </p>
              </div>
            </div>

            {/* Science Section */}
            <div className="space-y-4">
              <h3 className="text-2xl font-bold text-gray-900">Science Has Good News</h3>

              <div className="space-y-1 text-gray-600 text-lg">
                <p>
                  Your mind isn't fixed—it's flexible. Studies confirm that small daily habits can literally rewire your
                  brain from negativity and self-doubt toward positivity, happiness, confidence, and real progress.
                </p>
              </div>

              <p className="text-gray-600 text-lg font-semibold">
                That's exactly why we created Positivity Push—your personal AI coach, interacting with you daily via
                WhatsApp:
              </p>

              <div className="space-y-4">
                <div className="flex items-start space-x-3">
                  <span className="text-xl">✨</span>
                  <div>
                    <p className="font-semibold text-gray-900 text-lg">Daily Positive Affirmations:</p>
                    <p className="text-gray-600 text-lg">
                      Proven by neuroscience to quiet self-doubt, reduce anxiety, and build lasting confidence.
                    </p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <span className="text-xl">🙏</span>
                  <div>
                    <p className="font-semibold text-gray-900 text-lg">Gratitude Prompts:</p>
                    <p className="text-gray-600 text-lg">
                      Scientifically shown to boost happiness, optimism, and resilience while reducing stress.
                    </p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <span className="text-xl">📊</span>
                  <div>
                    <p className="font-semibold text-gray-900 text-lg">Daily Accountability Check-ins:</p>
                    <p className="text-gray-600 text-lg">
                      Leveraging behavioral science to move you from intention to action, and from dreams to reality.
                    </p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <span className="text-xl">📅</span>
                  <div>
                    <p className="font-semibold text-gray-900 text-lg">Weekly Check-In & Progress Snapshot:</p>
                    <p className="text-gray-600 text-lg">
                      A quick Sunday recap that highlights your wins, flags what slipped, and locks in next week's top
                      priority—so momentum never fades.
                    </p>
                  </div>
                </div>
              </div>

              <p className="text-gray-600 text-lg">
                Whether your goal is more wealth, better health, stronger relationships, or simply more confidence,
                peace, and happiness, Positivity Push daily support helps you build science-backed habits to strengthen
                your mindset, stay on track, and move closer to the life you truly want.
              </p>
            </div>

            {/* Final Message */}
            <p className="text-xl font-bold text-gray-900">
              You Are Stronger Than You Know. Closer Than You Think To The Life You Want.
            </p>

            {/* CTA + Trust Row */}
            <div className="space-y-4">
              <Button
                onClick={scrollToPricing}
                className="bg-[#00C48C] hover:bg-[#00A876] text-white font-bold px-8 py-4 rounded-xl text-lg"
              >
                ✅ LET'S BEGIN — I'M READY 💖 →
              </Button>
            </div>
          </div>

          {/* Right Column - Before/Solution/After Images */}
          <div className="flex justify-center">
            <div className="space-y-6">
              {/* Before Image - Exhausted */}
              <div className="relative">
                <Image
                  src="/exhausted-final.png"
                  alt="Close-up portrait of a woman in deep distress, hand pressed to forehead, eyes closed, showing the pain of negative self-talk and mental exhaustion"
                  width={350}
                  height={500}
                  className="object-cover rounded-2xl shadow-lg"
                />
              </div>

              {/* Solution - Brand Logo with Arrows */}
              <div className="relative flex justify-center">
                <Image
                  src="/positivity-push-with-arrows.png"
                  alt="Positivity Push transformation flow with directional arrows showing the journey from struggle to solution to success"
                  width={300}
                  height={400}
                  className="object-contain"
                />
              </div>

              {/* After Image - Happy */}
              <div className="relative">
                <Image
                  src="/happy-final.png"
                  alt="Same woman transformed - confident smile, bright eyes, hands positioned confidently, radiating inner peace and happiness after using Positivity Push"
                  width={350}
                  height={500}
                  className="object-cover rounded-2xl shadow-lg"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
