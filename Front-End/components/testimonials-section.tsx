"use client"

import { ChevronLeft, ChevronRight, Play } from "lucide-react"
import { useState } from "react"

export function TestimonialsSection() {
  const [currentIndex, setCurrentIndex] = useState(0)

  const testimonials = [
    {
      name: "Sarah",
      role: "E-commerce Founder",
      quote:
        "AI-Briefly saves me hours every week. I get exactly the AI updates I need for my business, with actionable tips I can implement immediately.",
      avatar: "/placeholder.svg?height=48&width=48",
      isVideo: false,
    },
    {
      name: "Marcus",
      role: "Digital Marketing Director",
      quote:
        'The "so-what?" tips are game-changing. Instead of just reading news, I get concrete steps to improve my marketing campaigns with AI.',
      avatar: "/placeholder.svg?height=48&width=48",
      isVideo: true,
    },
    {
      name: "Lisa",
      role: "Tech Startup CEO",
      quote:
        "Having AI news delivered directly to WhatsApp is brilliant. No new apps, no distractions – just the insights I need when I need them.",
      avatar: "/placeholder.svg?height=48&width=48",
      isVideo: false,
    },
    {
      name: "David",
      role: "Product Manager",
      quote:
        "The personalization is incredible. AI-Briefly learns what matters to my product roadmap and filters everything else out.",
      avatar: "/placeholder.svg?height=48&width=48",
      isVideo: false,
    },
  ]

  const nextTestimonial = () => {
    setCurrentIndex((prev) => (prev + 1) % testimonials.length)
  }

  const prevTestimonial = () => {
    setCurrentIndex((prev) => (prev - 1 + testimonials.length) % testimonials.length)
  }

  return (
    <section className="min-h-[420px] bg-white py-16">
      <div className="max-w-7xl mx-auto px-6">
        <h2 className="font-sans font-semibold text-4xl text-[#111111] text-center mb-16">What Users Are Saying</h2>

        <div className="relative max-w-6xl mx-auto">
          <div className="flex items-center justify-center space-x-8">
            <button
              onClick={prevTestimonial}
              className="p-2 rounded-full border border-[#E0E0E0] hover:bg-[#F9F9F9] transition-colors"
            >
              <ChevronLeft className="w-6 h-6 text-[#555555]" />
            </button>

            <div className="overflow-hidden w-full max-w-4xl">
              <div
                className="flex transition-transform duration-300 ease-in-out"
                style={{ transform: `translateX(-${currentIndex * 100}%)` }}
              >
                {testimonials.map((testimonial, index) => (
                  <div key={index} className="w-full flex-shrink-0 px-4">
                    <div className="bg-[#F9F9F9] rounded-lg p-6 h-[240px] flex flex-col relative">
                      {testimonial.isVideo && (
                        <div className="absolute top-4 right-4">
                          <div className="w-8 h-8 bg-[#00C48C] rounded-full flex items-center justify-center">
                            <Play className="w-4 h-4 text-white fill-white" />
                          </div>
                        </div>
                      )}

                      <div className="flex items-center space-x-4 mb-4">
                        <div className="w-12 h-12 bg-gray-300 rounded-full"></div>
                        <div>
                          <div className="font-sans font-medium text-lg text-[#111111]">{testimonial.name}</div>
                          <div className="text-[#555555] font-sans text-sm">{testimonial.role}</div>
                        </div>
                      </div>

                      <p className="text-[#555555] font-sans text-base flex-1 leading-relaxed">"{testimonial.quote}"</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <button
              onClick={nextTestimonial}
              className="p-2 rounded-full border border-[#E0E0E0] hover:bg-[#F9F9F9] transition-colors"
            >
              <ChevronRight className="w-6 h-6 text-[#555555]" />
            </button>
          </div>

          {/* Dots indicator */}
          <div className="flex justify-center space-x-2 mt-8">
            {testimonials.map((_, index) => (
              <button
                key={index}
                onClick={() => setCurrentIndex(index)}
                className={`w-2 h-2 rounded-full transition-colors ${
                  index === currentIndex ? "bg-[#00C48C]" : "bg-[#E0E0E0]"
                }`}
              />
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
