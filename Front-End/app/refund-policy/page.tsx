import Link from "next/link"

export default function RefundPolicyPage() {
  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="mb-8">
          <Link href="/" className="text-[#00C48C] hover:text-[#00A876] font-medium mb-4 inline-block">
            ← Back to Home
          </Link>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Refund & Cancellation Policy</h1>
          <p className="text-gray-600">Last updated: 29 June 2025</p>
        </div>

        <div className="prose prose-lg max-w-none">
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">1. 30-Day Money-Back Guarantee</h2>
            <p className="text-gray-700 mb-4">
              Try Positivity Push risk-free. If you're not 100% satisfied within 30 days of your first payment, email
              support@positivitypush.com and we'll issue a full refund—no questions asked.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">2. How to Cancel</h2>
            <p className="text-gray-700 mb-4">You can cancel at any time:</p>

            <div className="overflow-x-auto mb-4">
              <table className="min-w-full border border-gray-300">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="border border-gray-300 px-4 py-2 text-left font-semibold">Method</th>
                    <th className="border border-gray-300 px-4 py-2 text-left font-semibold">How</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td className="border border-gray-300 px-4 py-2">Email</td>
                    <td className="border border-gray-300 px-4 py-2">
                      Send "Cancel my subscription" to support@positivitypush.com
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <p className="text-gray-700">
              We'll confirm within 24 hours. Your plan stays active until the current billing period ends; no further
              charges will be made.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">3. What Happens After Cancellation</h2>
            <ul className="list-disc pl-6 text-gray-700 space-y-2">
              <li>Coaching messages continue until the paid period expires.</li>
              <li>You may reactivate at any time by resubscribing.</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">4. Refund Eligibility</h2>
            <p className="text-gray-700 mb-4">We grant full refunds for:</p>
            <ul className="list-disc pl-6 text-gray-700 space-y-2 mb-4">
              <li>Requests within the 30-day guarantee window</li>
              <li>Duplicate charges or billing errors</li>
              <li>Technical issues that prevent service access</li>
              <li>Proven unauthorised transactions</li>
            </ul>
            <p className="text-gray-700">
              Refund timeline: processed within 2 business days; funds usually appear in 5–7 business days (up to 10
              days for some banks). We'll email confirmation when complete.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">5. Non-Refundable Situations</h2>
            <p className="text-gray-700 mb-4">We cannot refund:</p>
            <ul className="list-disc pl-6 text-gray-700 space-y-2">
              <li>Requests made after the 30-day guarantee period</li>
              <li>Unused time within an active billing cycle</li>
              <li>"Change of mind" after the guarantee window</li>
              <li>Accounts terminated for violations of our Terms of Service</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">6. Renewal Reminders</h2>
            <p className="text-gray-700">
              We email and WhatsApp you 7 days before any renewal. Cancel or change plans any time before the renewal
              date—no surprise charges.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">7. Billing Issues</h2>
            <p className="text-gray-700">
              Spot a problem? Email support@positivitypush.com with your subscription details. We investigate and
              resolve billing errors within 48 hours; legitimate errors are refunded promptly.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">8. Pausing Your Subscription</h2>
            <p className="text-gray-700">
              We don't currently offer a pause feature. You may cancel and reactivate later, or contact support in
              special cases (medical or financial hardship) and we'll do our best to help.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">9. Contact</h2>
            <p className="text-gray-700 mb-2">
              Email:{" "}
              <a href="mailto:support@positivitypush.com" className="text-[#00C48C] hover:text-[#00A876]">
                support@positivitypush.com
              </a>
            </p>
            <p className="text-gray-700 mb-2">Subject: "Cancellation Request" or "Refund Request"</p>
            <p className="text-gray-700">We reply within 24 hours.</p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Our Commitment</h2>
            <p className="text-gray-700">
              Positivity Push exists to help you build a more positive, confident life. If we're not delivering that
              value, we'll make it right—or refund you in full.
            </p>
          </section>
        </div>
      </div>
    </div>
  )
}
