"use client"

import Image from "next/image"
import { Button } from "@/components/ui/button"
import { Star, Clock } from "lucide-react"
import { useState } from "react"

export function HeroProductSection() {
  const [selectedPlan, setSelectedPlan] = useState("6-month")
  const [currentSlide, setCurrentSlide] = useState(0)

  const slides = [
    {
      src: "/slide-1.png",
      alt: "Positivity Push - Morning motivation and goal accountability conversation with proposal encouragement",
    },
    {
      src: "/slide-2.png",
      alt: "Positivity Push - Gratitude practice and brightness check conversation showing mood lifting support",
    },
    {
      src: "/slide-3.png",
      alt: "Positivity Push - Motivational support conversation helping overcome tiredness and doubt with personal examples",
    },
    {
      src: "/slide-4.png",
      alt: "WhatsApp notifications showing daily motivational messages and positive affirmations on phone screen",
    },
    {
      src: "/slide-5.png",
      alt: "Positivity Push weekly reflection check-in conversation showing personalized coaching for goal accountability and honest self-reflection",
    },
  ]

  const goToSlide = (index: number) => {
    setCurrentSlide(index)
  }

  const benefits = [
    { icon: "😊", text: "Cultivate a Positive Mindset" },
    { icon: "💪", text: "Build Unshakeable Self-Confidance" },
    { icon: "🙏", text: "Practice Gratitude & Mindfulness" },
    { icon: "🎯", text: "Hit Your Goals with Smart Guidance" },
    { icon: "📊", text: "Stay Accountable & See Your Progress" },
    { icon: "💬", text: "No New App Needed—Everything Happens in WhatsApp" },
  ]

  return (
    <section className="bg-white py-8">
      <div className="max-w-7xl mx-auto px-4">
        {/* Mobile Layout - Content First, Then Images */}
        <div className="block lg:hidden">
          {/* Mobile Content Section */}
          <div className="space-y-6 mb-8">
            {/* Reviews */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="flex space-x-1">
                  {[...Array(5)].map((_, i) => (
                    <Star key={i} className="w-5 h-5 fill-[#00C48C] text-[#00C48C]" />
                  ))}
                </div>
              </div>
              <span className="text-[#00C48C] font-medium text-sm bg-teal-50/70 px-3 py-1 rounded-full">
                📚 Science-Backed
              </span>
            </div>

            {/* Product Title */}
            <h1 className="text-4xl font-bold text-gray-900">Positivity Push</h1>
            <p className="text-xl text-gray-700 -mt-2">Feel Happier, Stay Grateful And Hit Your Goals</p>
            {/* Mobile Images Section - Between title and description */}
            <div className="relative -mt-3">
              <div className="relative w-full h-[500px] rounded-3xl overflow-hidden">
                <Image
                  src={slides[currentSlide].src || "/placeholder.svg"}
                  alt={slides[currentSlide].alt}
                  fill
                  className="object-contain transition-opacity duration-500 rounded-3xl"
                  priority={currentSlide === 0}
                />
              </div>

              {/* Product Gallery Thumbnails - Mobile (Fixed to be squares) */}
              <div className="flex space-x-3 -mt-8 overflow-x-auto pb-2">
                {slides.map((slide, index) => (
                  <div
                    key={index}
                    className={`flex-shrink-0 w-20 h-20 rounded-lg overflow-hidden shadow-sm transition-all cursor-pointer ${
                      index === currentSlide
                        ? "border-2 border-[#00C48C]"
                        : "hover:border-2 hover:border-gray-300 opacity-70"
                    }`}
                    onClick={() => goToSlide(index)}
                  >
                    <Image
                      src={slide.src || "/placeholder.svg"}
                      alt={slide.alt}
                      width={80}
                      height={80}
                      className="object-cover w-full h-full"
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* Product Description */}
            <p className="text-gray-600 text-lg">
              From positive thoughts to achieved goals—your personal AI coach on WhatsApp helps you conquer self-doubt
              with science-backed positive thinking, raise your self-esteem and self confidance through daily gratitude,
              and stay accountable so every goal moves from idea to reality.
            </p>

            {/* Benefits */}
            <div className="space-y-3">
              {benefits.map((benefit, index) => (
                <div key={index} className="flex items-center space-x-3">
                  <span className="text-xl">{benefit.icon}</span>
                  <span className="text-gray-700">{benefit.text}</span>
                </div>
              ))}
            </div>

            {/* Bundle & Save */}
            <div
              id="pricing-mobile"
              className="border-2 border-gray-200 rounded-xl p-6 bg-gradient-to-br from-teal-50/60 to-emerald-50/60"
            >
              <div className="text-center mb-4">
                <h3 className="font-bold text-lg text-gray-900">SAVE & THRIVE</h3>
              </div>

              {/* Pricing Options */}
              <div className="space-y-4">
                {/* 6-Month Pack */}
                <div
                  className={`flex items-center justify-between p-4 bg-white rounded-lg border-2 relative cursor-pointer ${
                    selectedPlan === "6-month" ? "border-[#00C48C]" : "border-gray-200"
                  }`}
                  onClick={() => setSelectedPlan("6-month")}
                >
                  <div className="absolute -top-3 left-4 bg-[#00C48C] text-white px-2 py-1 rounded-full text-xs font-medium">
                    Best Value - Save 40%
                  </div>
                  <div className="flex items-center space-x-3">
                    <div
                      className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                        selectedPlan === "6-month" ? "bg-[#00C48C] border-[#00C48C]" : "border-gray-300"
                      }`}
                    >
                      {selectedPlan === "6-month" && <div className="w-2 h-2 bg-white rounded-full"></div>}
                    </div>
                    <div>
                      <p className="font-medium text-lg">6-Month Plan (Thrive)</p>
                      <p className="text-sm text-gray-500">€5.83/month ≈ €0.19/day</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-3xl font-bold text-[#00C48C]">€34.99</p>
                    <p className="text-sm text-gray-500 line-through">€58.32</p>
                  </div>
                </div>

                {/* 3-Month Pack */}
                <div
                  className={`flex items-center justify-between p-4 bg-white rounded-lg border cursor-pointer ${
                    selectedPlan === "3-month" ? "border-2 border-[#00C48C]" : "border-gray-200"
                  }`}
                  onClick={() => setSelectedPlan("3-month")}
                >
                  <div className="flex items-center space-x-3">
                    <div
                      className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                        selectedPlan === "3-month" ? "bg-[#00C48C] border-[#00C48C]" : "border-gray-300"
                      }`}
                    >
                      {selectedPlan === "3-month" && <div className="w-2 h-2 bg-white rounded-full"></div>}
                    </div>
                    <div>
                      <p className="font-medium text-lg">3-Month Plan (Starter)</p>
                      <p className="text-sm text-gray-500">€9.72/month</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-3xl font-bold text-[#00C48C]">€28.99</p>
                  </div>
                </div>

                {/* Guarantee Text */}
                <div className="text-center pt-2">
                  <span className="font-medium text-gray-700">✅ 30-Day Money-Back Guarantee 🛡️</span>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              {/* Sale Timer */}
              <div className="text-center py-3 bg-red-50 rounded-lg border border-red-200">
                <div className="flex items-center justify-center space-x-2 text-red-600">
                  <Clock className="w-4 h-4" />
                  <span className="font-medium">40% Off Ends Soon | Limited Time Offer 🔥</span>
                </div>
              </div>
            </div>

            {/* Add to Bag Button */}
            <Button className="w-full h-14 bg-[#00C48C] hover:bg-[#00A876] text-white font-bold text-lg rounded-xl">
              💖 START MY PLAN — RISK-FREE
            </Button>

            {/* Trust Badges */}
            <div className="grid grid-cols-3 gap-4 text-center">
              <div className="flex flex-col items-center space-y-2">
                <div className="w-16 h-16 rounded-full border border-[#00C48C] flex items-center justify-center">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path
                      d="M20 6L9 17L4 12"
                      stroke="#00C48C"
                      strokeWidth="2.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </div>
                <span className="text-sm font-medium">Cancel Anytime</span>
              </div>
              <div className="flex flex-col items-center space-y-2">
                <div className="w-16 h-16 rounded-full border border-[#00C48C] flex items-center justify-center">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="3" y="4" width="18" height="18" rx="2" stroke="#00C48C" strokeWidth="1.5" />
                    <path d="M16 2V6" stroke="#00C48C" strokeWidth="1.5" strokeLinecap="round" />
                    <path d="M8 2V6" stroke="#00C48C" strokeWidth="1.5" strokeLinecap="round" />
                    <path d="M3 10H21" stroke="#00C48C" strokeWidth="1.5" />
                    <text x="12" y="18" textAnchor="middle" fontSize="10" fontWeight="bold" fill="#00C48C">
                      30
                    </text>
                  </svg>
                </div>
                <span className="text-sm font-medium">30-Day Money-Back Guarantee</span>
              </div>
              <div className="flex flex-col items-center space-y-2">
                <div className="w-16 h-16 rounded-full border border-[#00C48C] flex items-center justify-center">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path
                      d="M16 11V7C16 4.79086 14.2091 3 12 3C9.79086 3 8 4.79086 8 7V11"
                      stroke="#00C48C"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                    />
                    <rect x="4" y="11" width="16" height="10" rx="2" stroke="#00C48C" strokeWidth="1.5" />
                    <circle cx="12" cy="16" r="1.5" fill="#00C48C" />
                  </svg>
                </div>
                <span className="text-sm font-medium">Data Privacy & Security (GDPR)</span>
              </div>
            </div>

            {/* Customer Testimonial */}
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <div className="w-12 h-12 bg-gray-300 rounded-full"></div>
                <div className="flex-1">
                  <p className="text-sm text-gray-700 italic">
                    "Positivity Push has been a game-changer for my confidence. The daily chats keep me focused and
                    motivated. I'm finally making progress on goals I've put off for years!"
                  </p>
                  <div className="flex items-center space-x-2 mt-2">
                    <div className="flex space-x-1">
                      {[...Array(5)].map((_, i) => (
                        <Star key={i} className="w-3 h-3 fill-[#00C48C] text-[#00C48C]" />
                      ))}
                    </div>
                    <span className="text-xs text-gray-500">- ✅ Jessica L. (New York, USA)</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Desktop Layout - Side by Side */}
        <div className="hidden lg:grid lg:grid-cols-2 gap-12 items-start">
          {/* Left Column - Product Image Slideshow */}
          <div className="relative -mt-16">
            <div className="relative w-full h-[700px] rounded-3xl overflow-hidden">
              <Image
                src={slides[currentSlide].src || "/placeholder.svg"}
                alt={slides[currentSlide].alt}
                fill
                className="object-contain transition-opacity duration-500 rounded-3xl"
                priority={currentSlide === 0}
              />
            </div>

            {/* Product Gallery Thumbnails - Desktop */}
            <div className="flex space-x-3 -mt-8 justify-start">
              {slides.map((slide, index) => (
                <div
                  key={index}
                  className={`w-24 h-24 rounded-lg overflow-hidden shadow-sm transition-all cursor-pointer ${
                    index === currentSlide
                      ? "border-2 border-[#00C48C]"
                      : "hover:border-2 hover:border-gray-300 opacity-70"
                  }`}
                  onClick={() => goToSlide(index)}
                >
                  <Image
                    src={slide.src || "/placeholder.svg"}
                    alt={slide.alt}
                    width={96}
                    height={96}
                    className="object-cover w-full h-full"
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Right Column - Product Details */}
          <div className="space-y-6">
            {/* Reviews */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="flex space-x-1">
                  {[...Array(5)].map((_, i) => (
                    <Star key={i} className="w-5 h-5 fill-[#00C48C] text-[#00C48C]" />
                  ))}
                </div>
              </div>
              <span className="text-[#00C48C] font-medium text-sm bg-teal-50/70 px-3 py-1 rounded-full">
                📚 Science-Backed
              </span>
            </div>

            {/* Product Title */}
            <h1 className="text-4xl font-bold text-gray-900">Positivity Push</h1>
            <p className="text-xl text-gray-700 -mt-2">Feel Happier, Stay Grateful And Hit Your Goals</p>

            {/* Product Description */}
            <p className="text-gray-600 text-lg">
              From positive thoughts to achieved goals—your personal AI coach on WhatsApp helps you conquer self-doubt
              with science-backed positive thinking, raise your self-esteem and self confidance through daily gratitude,
              and stay accountable so every goal moves from idea to reality.
            </p>

            {/* Benefits */}
            <div className="space-y-3">
              {benefits.map((benefit, index) => (
                <div key={index} className="flex items-center space-x-3">
                  <span className="text-xl">{benefit.icon}</span>
                  <span className="text-gray-700">{benefit.text}</span>
                </div>
              ))}
            </div>

            {/* Bundle & Save */}
            <div
              className="border-2 border-gray-200 rounded-xl p-6 bg-gradient-to-br from-teal-50/60 to-emerald-50/60"
              id="pricing-desktop"
            >
              <div className="text-center mb-4">
                <h3 className="font-bold text-lg text-gray-900">SAVE & THRIVE</h3>
              </div>

              {/* Pricing Options */}
              <div className="space-y-4">
                {/* 6-Month Pack */}
                <div
                  className={`flex items-center justify-between p-4 bg-white rounded-lg border-2 relative cursor-pointer ${
                    selectedPlan === "6-month" ? "border-[#00C48C]" : "border-gray-200"
                  }`}
                  onClick={() => setSelectedPlan("6-month")}
                >
                  <div className="absolute -top-3 left-4 bg-[#00C48C] text-white px-2 py-1 rounded-full text-xs font-medium">
                    Best Value - Save 40%
                  </div>
                  <div className="flex items-center space-x-3">
                    <div
                      className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                        selectedPlan === "6-month" ? "bg-[#00C48C] border-[#00C48C]" : "border-gray-300"
                      }`}
                    >
                      {selectedPlan === "6-month" && <div className="w-2 h-2 bg-white rounded-full"></div>}
                    </div>
                    <div>
                      <p className="font-medium text-lg">6-Month Plan (Thrive)</p>
                      <p className="text-sm text-gray-500">€5.83/month ≈ €0.19/day</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-3xl font-bold text-[#00C48C]">€34.99</p>
                    <p className="text-sm text-gray-500 line-through">€58.32</p>
                  </div>
                </div>

                {/* 3-Month Pack */}
                <div
                  className={`flex items-center justify-between p-4 bg-white rounded-lg border cursor-pointer ${
                    selectedPlan === "3-month" ? "border-2 border-[#00C48C]" : "border-gray-200"
                  }`}
                  onClick={() => setSelectedPlan("3-month")}
                >
                  <div className="flex items-center space-x-3">
                    <div
                      className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                        selectedPlan === "3-month" ? "bg-[#00C48C] border-[#00C48C]" : "border-gray-300"
                      }`}
                    >
                      {selectedPlan === "3-month" && <div className="w-2 h-2 bg-white rounded-full"></div>}
                    </div>
                    <div>
                      <p className="font-medium text-lg">3-Month Plan (Starter)</p>
                      <p className="text-sm text-gray-500">€9.72/month</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-3xl font-bold text-[#00C48C]">€28.99</p>
                  </div>
                </div>

                {/* Guarantee Text */}
                <div className="text-center pt-2">
                  <span className="font-medium text-gray-700">✅ 30-Day Money-Back Guarantee 🛡️</span>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              {/* Sale Timer */}
              <div className="text-center py-3 bg-red-50 rounded-lg border border-red-200">
                <div className="flex items-center justify-center space-x-2 text-red-600">
                  <Clock className="w-4 h-4" />
                  <span className="font-medium">40% Off Ends Soon | Limited Time Offer 🔥</span>
                </div>
              </div>
            </div>

            {/* Add to Bag Button */}
            <Button className="w-full h-14 bg-[#00C48C] hover:bg-[#00A876] text-white font-bold text-lg rounded-xl">
              💖 START MY PLAN — RISK-FREE
            </Button>

            {/* Trust Badges */}
            <div className="grid grid-cols-3 gap-4 text-center">
              <div className="flex flex-col items-center space-y-2">
                <div className="w-16 h-16 rounded-full border border-[#00C48C] flex items-center justify-center">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path
                      d="M20 6L9 17L4 12"
                      stroke="#00C48C"
                      strokeWidth="2.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </div>
                <span className="text-sm font-medium">Cancel Anytime</span>
              </div>
              <div className="flex flex-col items-center space-y-2">
                <div className="w-16 h-16 rounded-full border border-[#00C48C] flex items-center justify-center">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="3" y="4" width="18" height="18" rx="2" stroke="#00C48C" strokeWidth="1.5" />
                    <path d="M16 2V6" stroke="#00C48C" strokeWidth="1.5" strokeLinecap="round" />
                    <path d="M8 2V6" stroke="#00C48C" strokeWidth="1.5" strokeLinecap="round" />
                    <path d="M3 10H21" stroke="#00C48C" strokeWidth="1.5" />
                    <text x="12" y="18" textAnchor="middle" fontSize="10" fontWeight="bold" fill="#00C48C">
                      30
                    </text>
                  </svg>
                </div>
                <span className="text-sm font-medium">30-Day Money-Back Guarantee</span>
              </div>
              <div className="flex flex-col items-center space-y-2">
                <div className="w-16 h-16 rounded-full border border-[#00C48C] flex items-center justify-center">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path
                      d="M16 11V7C16 4.79086 14.2091 3 12 3C9.79086 3 8 4.79086 8 7V11"
                      stroke="#00C48C"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                    />
                    <rect x="4" y="11" width="16" height="10" rx="2" stroke="#00C48C" strokeWidth="1.5" />
                    <circle cx="12" cy="16" r="1.5" fill="#00C48C" />
                  </svg>
                </div>
                <span className="text-sm font-medium">Data Privacy & Security (GDPR)</span>
              </div>
            </div>

            {/* Customer Testimonial */}
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <div className="w-12 h-12 bg-gray-300 rounded-full"></div>
                <div className="flex-1">
                  <p className="text-sm text-gray-700 italic">
                    "Positivity Push has been a game-changer for my confidence. The daily chats keep me focused and
                    motivated. I'm finally making progress on goals I've put off for years!"
                  </p>
                  <div className="flex items-center space-x-2 mt-2">
                    <div className="flex space-x-1">
                      {[...Array(5)].map((_, i) => (
                        <Star key={i} className="w-3 h-3 fill-[#00C48C] text-[#00C48C]" />
                      ))}
                    </div>
                    <span className="text-xs text-gray-500">- ✅ Jessica L. (New York, USA)</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
