export function WhyChooseSection() {
  return (
    <section className="bg-gray-50 py-16">
      <div className="max-w-7xl mx-auto px-4">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          {/* Left Column - Features */}
          <div className="space-y-12">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 mb-2">
                Your Daily Coach to Feel Supported, Stay Accountable & Achieve What Matters 💖
              </h2>
            </div>

            {/* Feature 1 */}
            <div className="border-l-4 border-[#00C48C] pl-6">
              <h3 className="text-2xl font-bold text-gray-900 mb-3">💬 24/7 Motivation, Right in WhatsApp</h3>
              <p className="text-gray-600 text-lg leading-relaxed">
                Feeling overwhelmed, stuck, or just low on energy? Your AI companion is always just a message away—ready
                with encouragement, perspective, or a quick mindset reset whenever you need it.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="border-l-4 border-[#00C48C] pl-6">
              <h3 className="text-2xl font-bold text-gray-900 mb-3">🎯 Affirmations & Coaching—Tailored to You</h3>
              <p className="text-gray-600 text-lg leading-relaxed">
                No generic fluff. Every message is personalized to your goals, your mindset, and what you're actually
                going through. It's like having a coach who always knows the right thing to say.
              </p>
            </div>

            {/* Feature 2.5 - Daily Goal & Habit Accountability */}
            <div className="border-l-4 border-[#00C48C] pl-6">
              <h3 className="text-2xl font-bold text-gray-900 mb-3">✅ Daily Goal & Habit Accountability</h3>
              <p className="text-gray-600 text-lg leading-relaxed">
                Stay aligned with what matters most. Every day, your AI coach checks in on the specific goals and habits
                you've set—helping you stay consistent, focused, and committed. Small steps. Real progress. Daily.
              </p>
            </div>

            {/* Feature 2.75 - Weekly Reflection & Accountability Check-in */}
            <div className="border-l-4 border-[#00C48C] pl-6">
              <h3 className="text-2xl font-bold text-gray-900 mb-3">📅 Weekly Reflection & Accountability Check-in</h3>
              <p className="text-gray-600 text-lg leading-relaxed">
                Each week, take a moment for deeper reflection. Look back, acknowledge your wins and challenges, and
                thoughtfully define your next steps. This weekly check-in helps you build clarity, consistency, and
                momentum towards the life you truly want.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="border-l-4 border-[#00C48C] pl-6">
              <h3 className="text-2xl font-bold text-gray-900 mb-3">🧠 Built With Memory. Feels Like It Knows You.</h3>
              <p className="text-gray-600 text-lg leading-relaxed">
                Thanks to advanced memory tech, your AI coach remembers what you're working on—your wins, your
                struggles, your goals. So each interaction builds on the last, creating deeper, smarter support over
                time.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="border-l-4 border-[#00C48C] pl-6">
              <h3 className="text-2xl font-bold text-gray-900 mb-3">📱 No New Apps. No New Habits.</h3>
              <p className="text-gray-600 text-lg leading-relaxed">
                Positivity Push works right inside WhatsApp. No downloads. No logins. No friction. Just open your
                messages and feel the shift—anytime, anywhere.
              </p>
            </div>
          </div>

          {/* Right Column - iPhone Mockup */}
          <div className="flex justify-center">
            <div className="relative">
              <div className="w-[350px] h-[700px] bg-black rounded-[3rem] p-2 shadow-2xl">
                <div className="w-full h-full bg-white rounded-[2.5rem] overflow-hidden relative">
                  {/* Status Bar */}
                  <div className="flex justify-between items-center px-6 py-3 bg-white">
                    <span className="text-sm font-semibold">9:41</span>
                    <div className="flex space-x-1">
                      <div className="w-4 h-2 bg-black rounded-sm"></div>
                      <div className="w-4 h-2 bg-black rounded-sm"></div>
                      <div className="w-4 h-2 bg-black rounded-sm"></div>
                      <div className="w-6 h-3 border border-black rounded-sm"></div>
                    </div>
                  </div>

                  {/* WhatsApp Header */}
                  <div className="flex items-center px-4 py-3 bg-[#00C48C] text-white">
                    <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center mr-3">
                      <span className="text-[#00C48C] font-bold text-xl">✨</span>
                    </div>
                    <div>
                      <h4 className="font-semibold">Positivity Push</h4>
                      <p className="text-xs opacity-90">Online</p>
                    </div>
                  </div>

                  {/* Chat Content */}
                  <div className="p-4 space-y-3 bg-gray-50 h-full overflow-hidden">
                    {/* AI Message 1 */}
                    <div className="flex items-start space-x-2">
                      <div className="bg-white rounded-lg p-3 shadow-sm max-w-[260px] relative">
                        <div className="flex items-center mb-2">
                          <div className="w-2 h-2 bg-[#00C48C] rounded-full mr-2"></div>
                          <span className="font-semibold text-[#00C48C] text-sm">Positivity Push:</span>
                        </div>
                        <p className="text-gray-800 text-sm leading-relaxed mb-2">
                          Hey Sandra 👋<br />
                          Before we dive into next week…
                          <br />
                          Let's take a sec to look back.
                        </p>
                        <p className="text-gray-800 text-sm leading-relaxed">
                          You've been showing up at the gym almost every day lately—seriously, that's something to be
                          proud of.
                        </p>
                        <div className="absolute bottom-0 left-0 w-0 h-0 border-l-[8px] border-l-transparent border-r-[8px] border-r-white border-t-[8px] border-t-white transform translate-y-full -translate-x-1"></div>
                        <p className="text-gray-400 text-xs mt-2">2:15 PM</p>
                      </div>
                    </div>

                    {/* AI Message 2 */}
                    <div className="flex items-start space-x-2">
                      <div className="bg-white rounded-lg p-3 shadow-sm max-w-[260px] relative">
                        <div className="flex items-center mb-2">
                          <div className="w-2 h-2 bg-[#00C48C] rounded-full mr-2"></div>
                          <span className="font-semibold text-[#00C48C] text-sm">Positivity Push:</span>
                        </div>
                        <p className="text-gray-800 text-sm leading-relaxed">
                          So tell me—
                          <br />
                          What felt good this week?
                          <br />
                          What threw you off a bit?
                          <br />
                          What would you want to handle differently next time?
                        </p>
                        <div className="absolute bottom-0 left-0 w-0 h-0 border-l-[8px] border-l-transparent border-r-[8px] border-r-white border-t-[8px] border-t-white transform translate-y-full -translate-x-1"></div>
                        <p className="text-gray-400 text-xs mt-2">2:16 PM</p>
                      </div>
                    </div>

                    {/* User Response */}
                    <div className="flex justify-end">
                      <div className="bg-[#dcf8c6] rounded-lg p-3 max-w-[220px] relative">
                        <p className="text-gray-800 text-sm leading-relaxed">
                          Yeah… I'm proud I stuck with the gym.
                          <br />
                          And Thursday could've been better, but I'm trying not to beat myself up.
                        </p>
                        <div className="absolute bottom-0 right-0 w-0 h-0 border-l-[8px] border-l-[#dcf8c6] border-r-[8px] border-r-transparent border-t-[8px] border-t-[#dcf8c6] transform translate-y-full translate-x-1"></div>
                        <p className="text-gray-400 text-xs text-right mt-2">2:18 PM</p>
                      </div>
                    </div>

                    {/* AI Response */}
                    <div className="flex items-start space-x-2">
                      <div className="bg-white rounded-lg p-3 shadow-sm max-w-[260px] relative">
                        <div className="flex items-center mb-2">
                          <div className="w-2 h-2 bg-[#00C48C] rounded-full mr-2"></div>
                          <span className="font-semibold text-[#00C48C] text-sm">Positivity Push:</span>
                        </div>
                        <p className="text-gray-800 text-sm leading-relaxed">
                          That's the right energy.
                          <br />
                          Small wins build trust with yourself. That's how real change sticks.
                        </p>
                        <div className="absolute bottom-0 left-0 w-0 h-0 border-l-[8px] border-l-transparent border-r-[8px] border-r-white border-t-[8px] border-t-white transform translate-y-full -translate-x-1"></div>
                        <p className="text-gray-400 text-xs mt-2">2:19 PM</p>
                      </div>
                    </div>
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
