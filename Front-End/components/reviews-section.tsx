import { Star } from "lucide-react"

export function ReviewsSection() {
  const reviews = [
    {
      name: "Jessica L.",
      verified: true,
      rating: 5,
      text: "This app is like having a cheerleader in your pocket. The daily messages are exactly what I need to hear. My self-talk has become so much more positive! 🤩",
      image: "/placeholder.svg?height=80&width=80",
    },
    {
      name: "Mike P.",
      verified: true,
      rating: 5,
      text: "I was skeptical at first, but Positivity Push has been a game-changer for my productivity. The accountability check-ins keep me on track with my goals. I've accomplished more in the last month than I did in the previous six.",
      image: "/placeholder.svg?height=80&width=80",
    },
    {
      name: "Chloe H.",
      verified: true,
      rating: 5,
      text: "I struggle with anxiety, and having a non-judgmental AI to chat with anytime has been incredibly helpful. It helps me reframe my thoughts and focus on gratitude. So glad I tried this.",
      image: "/placeholder.svg?height=80&width=80",
    },
    {
      name: "David K.",
      verified: true,
      rating: 5,
      text: "Simple, effective, and lives in the app I use most. My mindset feels lighter and more optimistic. Can't wait to see my continued growth!",
      image: "/placeholder.svg?height=80&width=80",
    },
    {
      name: "Emma T.",
      verified: true,
      rating: 5,
      text: "This is literally a game changer for my mental well-being. I have used this product for months and recommended it to all my friends. It's amazing how much of a difference a little daily positivity can make.",
      image: "/placeholder.svg?height=80&width=80",
    },
  ]

  return (
    <section className="bg-gray-50 py-16">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-4">
            <div className="flex space-x-1">
              {[...Array(5)].map((_, i) => (
                <Star key={i} className="w-6 h-6 fill-[#00C48C] text-[#00C48C]" />
              ))}
            </div>
            <span className="text-lg font-semibold">1,200+ Reviews</span>
          </div>
          <button className="text-gray-600 hover:text-gray-800">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {reviews.map((review, index) => (
            <div key={index} className="bg-white rounded-lg p-6 shadow-sm">
              <div className="flex items-center space-x-3 mb-4">
                <div className="w-12 h-12 bg-gray-200 rounded-full"></div>
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-semibold text-gray-900">{review.name}</span>
                    {review.verified && (
                      <div className="w-4 h-4 bg-blue-500 rounded-full flex items-center justify-center">
                        <span className="text-white text-xs">✓</span>
                      </div>
                    )}
                  </div>
                  <span className="text-sm text-gray-500">Verified</span>
                </div>
              </div>

              <div className="flex space-x-1 mb-3">
                {[...Array(review.rating)].map((_, i) => (
                  <Star key={i} className="w-4 h-4 fill-[#00C48C] text-[#00C48C]" />
                ))}
              </div>

              <p className="text-gray-700 text-sm leading-relaxed">
                {review.text.length > 150 ? `${review.text.substring(0, 150)}...` : review.text}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
