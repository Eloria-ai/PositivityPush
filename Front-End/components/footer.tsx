import { Mail, Facebook, Instagram } from "lucide-react"

export function Footer() {
  return (
    <footer className="bg-gray-900 text-white py-16">
      <div className="max-w-7xl mx-auto px-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Contact Us */}
          <div>
            <h4 className="text-[#00C48C] font-semibold mb-4 uppercase tracking-wide text-sm">CONTACT US</h4>
            <a href="mailto:hello@positivitypush.com" className="text-gray-300 hover:text-white transition-colors">
              hello@positivitypush.com
            </a>
          </div>

          {/* Customer Care */}
          <div>
            <h4 className="text-[#00C48C] font-semibold mb-4 uppercase tracking-wide text-sm">CUSTOMER CARE</h4>
            <div className="space-y-2">
              <a href="/terms" className="block text-gray-300 hover:text-white transition-colors">
                Terms of Service
              </a>
              <a href="/privacy" className="block text-gray-300 hover:text-white transition-colors">
                Privacy Policy
              </a>
              <a href="/refund-policy" className="block text-gray-300 hover:text-white transition-colors">
                Refund & Cancellation Policy
              </a>
            </div>
          </div>

          {/* Socials */}
          <div>
            <h4 className="text-[#00C48C] font-semibold mb-4 uppercase tracking-wide text-sm">SOCIALS</h4>
            <div className="flex space-x-4">
              <a
                href="mailto:hello@positivitypush.com"
                className="text-gray-300 hover:text-white transition-colors"
                aria-label="Email"
              >
                <Mail className="w-6 h-6" />
                <span className="sr-only">Email</span>
              </a>
              <a href="#" className="text-gray-300 hover:text-white transition-colors" aria-label="Facebook">
                <Facebook className="w-6 h-6" />
                <span className="sr-only">Facebook</span>
              </a>
              <a href="#" className="text-gray-300 hover:text-white transition-colors" aria-label="Instagram">
                <Instagram className="w-6 h-6" />
                <span className="sr-only">Instagram</span>
              </a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  )
}
