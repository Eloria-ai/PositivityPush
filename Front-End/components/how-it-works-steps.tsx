import { CreditCard, MessageCircle, MessageSquare } from "lucide-react"

export function HowItWorksSteps() {
  return (
    <section className="bg-gradient-to-br from-teal-50/60 to-emerald-50/60 py-16">
      <div className="max-w-7xl mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">✨ How It Works</h2>
          <p className="text-gray-600 text-lg">Start building a better life—one message at a time.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-12 max-w-6xl mx-auto">
          {/* Step 1 */}
          <div className="text-center relative">
            <div className="flex justify-center mb-6">
              <div className="w-20 h-20 bg-[#00C48C] rounded-2xl flex items-center justify-center shadow-lg">
                <CreditCard className="w-10 h-10 text-white" />
              </div>
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-4">Sign Up & Subscribe</h3>
            <p className="text-gray-600 leading-relaxed">
              Choose your plan and get instant access to your personal AI coach on WhatsApp—no app downloads, no
              friction.
            </p>

            {/* Decorative icon */}
            <div className="hidden md:block absolute -right-6 top-8">
              <div className="w-8 h-8 flex items-center justify-center">
                <div className="w-6 h-6 border-2 border-[#00C48C] border-dashed rounded-full flex items-center justify-center">
                  <div className="w-2 h-2 bg-[#00C48C] rounded-full"></div>
                </div>
              </div>
            </div>
          </div>

          {/* Step 2 */}
          <div className="text-center relative">
            <div className="flex justify-center mb-6">
              <div className="w-20 h-20 bg-[#00C48C] rounded-2xl flex items-center justify-center shadow-lg">
                <MessageCircle className="w-10 h-10 text-white" />
              </div>
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-4">Receive Your Daily Positivity Push</h3>
            <p className="text-gray-600 leading-relaxed">
              Get science-backed messages to become positive, lift your mood, keep you grateful, and reconnect you to
              the goals that actually matter—right when you need them.
            </p>

            {/* Decorative icon */}
            <div className="hidden md:block absolute -right-6 top-8">
              <div className="w-8 h-8 flex items-center justify-center">
                <div className="w-6 h-6 border-2 border-[#00C48C] border-dashed rounded-full flex items-center justify-center">
                  <div className="w-2 h-2 bg-[#00C48C] rounded-full"></div>
                </div>
              </div>
            </div>
          </div>

          {/* Step 3 */}
          <div className="text-center">
            <div className="flex justify-center mb-6">
              <div className="w-20 h-20 bg-[#00C48C] rounded-2xl flex items-center justify-center shadow-lg">
                <MessageSquare className="w-10 h-10 text-white" />
              </div>
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-4">Chat Anytime for Support</h3>
            <p className="text-gray-600 leading-relaxed">
              Feeling stuck? Need a boost? Your AI companion is always here to support, motivate, and help you stay on
              track toward the life you truly want.
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}
