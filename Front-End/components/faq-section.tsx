import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"

export function FaqSection() {
  const faqs = [
    {
      question: "How does Positivity Push work on WhatsApp?",
      answer:
        "After you subscribe, you’ll receive a link that opens a private chat. Say “Hi,” and your AI coach comes online. From then on you’ll get short, personalised messages through the day—no new apps.",
    },
    {
      question: "What exactly do I get for the subscription fee?",
      answer: (
        <div className="space-y-2">
          <p>• Daily mindset boosts (affirmations + quick micro-lessons)</p>
          <p>• Nightly gratitude & reflection prompts</p>
          <p>• Accountability nudges tied to your goals</p>
          <p>• Weekly progress reports that highlight wins & next-step focus</p>
          <p>• 24/7 on-demand chat for motivation or clarity</p>
          <p>• Memory-based replies that get smarter the more you use it</p>
        </div>
      ),
    },
    {
      question: "Is Positivity Push backed by science?",
      answer:
        "Yes. Our content is based on peer-reviewed research showing that daily affirmations reduce negative self-talk, gratitude practice boosts happiness, and accountability check-ins double goal-completion rates. We turn those findings into quick WhatsApp conversations you can actually stick with.",
    },
    {
      question: "What results should I expect?",
      answer:
        "Based on the research behind our app, most people start to feel lighter, more focused, and more consistent within about two weeks of daily affirmations, gratitude prompts, and accountability check-ins.",
    },
    {
      question: "Is this a one-time purchase or a subscription?",
      answer:
        "Choose a 3-month or 6-month plan—whichever feels right for your journey—and cancel anytime with a quick WhatsApp message. We’ll always send you a friendly reminder before your plan renews, so you have plenty of time to switch plans, or cancel if you need to.",
    },
    {
      question: "Is my data private and secure?",
      answer:
        "Yes. Chats are end-to-end encrypted by WhatsApp and stored in a secure, GDPR-compliant database. We never sell or share your data, and you can delete your history any time.",
    },
    {
      question: "Can I cancel or pause whenever I want?",
      answer:
        "Absolutely. Just send an email to support@positivitypush.com and we’ll cancel your subscription right away—no hoops, no hassle.",
    },
    {
      question: "How does the 30-day money-back guarantee work?",
      answer:
        "We're confident you'll love the positive changes. If you're not 100% satisfied within the first 30 days, just send us an email, and we'll issue a full refund. No questions asked.",
    },
    {
      question: "How is this different from other mindset apps?",
      answer:
        "Three things: 1) It's on WhatsApp, so there's zero friction. 2) It's conversational and personalized with memory, so it feels like a real coach who knows you. 3) It's grounded in proven behavioral science to create real, lasting change, not just temporary inspiration.",
    },
  ]

  return (
    <section className="bg-white py-16">
      <div className="max-w-4xl mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">Frequently Asked Questions</h2>
          <p className="text-gray-600 text-lg">
            Have questions? We've got answers. Here are some of the most common things people ask.
          </p>
        </div>
        <Accordion type="single" collapsible className="w-full">
          {faqs.map((faq, index) => (
            <AccordionItem key={index} value={`item-${index}`}>
              <AccordionTrigger className="text-lg font-semibold text-left hover:no-underline">
                {faq.question}
              </AccordionTrigger>
              <AccordionContent className="text-base text-gray-600 leading-relaxed">{faq.answer}</AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </section>
  )
}
